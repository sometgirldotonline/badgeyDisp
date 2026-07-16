**this was written by claude, i am lazy, this probably was documented elsewhere but ehh**

# Badge Serial Protocol Reference

Reverse-engineered from `badge-paint`'s `app.js` (the WebSerial-based painter
app). This covers everything needed to send a frame to the badge from a
long-running client; it does not cover the one-time MicroPython/firmware
install flow (see Appendix if you ever need to reflash).

## Transport

- USB CDC serial, **115200 baud, 8N1**.
- Vendor ID **`0x2e8a`** (Raspberry Pi Foundation) - use this to find the
  device rather than hardcoding a path/COM port.
- **You must assert DTR and RTS after opening the port.** MicroPython's
  USB-CDC implementation silently drops all output until DTR is asserted -
  the badge will still draw the frame you send, but you'll never see its
  `OK`/`ERR` reply, and your client will hang waiting for it. This is not
  optional and not documented anywhere on the firmware side; it's a
  MicroPython quirk the original app works around.

In Rust, using the [`serialport`](https://crates.io/crates/serialport) crate:

```rust
let mut port = serialport::new(path, 115_200)
    .timeout(Duration::from_millis(200))
    .open()?;
port.write_data_terminal_ready(true)?;
port.write_request_to_send(true)?;
```

## Frame format

One frame = a 9-byte header immediately followed by the packed bitmap bytes,
written as a single logical write (back-to-back writes are fine, there's no
inter-byte delay requirement).

### Header (9 bytes)

| Bytes | Field | Notes |
|---|---|---|
| 0-4 | `"BPNT1"` | literal ASCII, badge-paint's frame magic |
| 5-6 | `PW` | portrait width, big-endian u16 |
| 7-8 | `PH` | portrait height, big-endian u16 |

For the 296x152 badge screen, the wire format is **portrait**: `PW = 152`,
`PH = 296` (i.e. the landscape image gets rotated 90° before packing - see
below). Don't send 296/152 as the header values, that'll desync the parser
expecting `(PW*PH)/8` payload bytes.

### Payload

`(PW * PH) / 8` bytes of packed 1bpp bitmap data, described below. For
152x296 that's `152 * 296 / 8 = 5624` bytes.

**Note:** this packing scheme requires `PW` to be a multiple of 8 (152 is).
If you ever change panel dimensions, keep that constraint or the bit math
breaks.

## Bitmap encoding

Two things happen before you get to a byte array: a 90° rotation from your
natural landscape framebuffer into the panel's portrait orientation, and
then 1bpp packing.

### 1. Rotation (landscape source -> portrait output)

If your renderer produces a landscape image at `W=296, H=152` (row-major,
one byte/pixel or RGBA, doesn't matter which - just something you can index
by `(x, y)`), map each portrait output pixel back to a source pixel like
this:

```
PW = H   // 152
PH = W   // 296

for py in 0..PH {
    for px in 0..PW {
        let lx = py;
        let ly = H - 1 - px;
        let is_white = source_pixel(lx, ly) > threshold;
        // pack (px, py) below
    }
}
```

This is a 90° rotation plus a flip, chosen so the image comes out upright on
the physical badge - don't "simplify" it to a plain transpose, it'll come
out mirrored or upside down.

### 2. Packing (1bpp, MSB-first, 1 = white)

Bits are packed row-major across the whole portrait image, 8 pixels per
byte, **MSB first**, **1 = white, 0 = black**:

```
byte_index = (py * PW + px) >> 3
bit_mask   = 0x80 >> (px & 7)
if is_white { out[byte_index] |= bit_mask }
// else leave the bit as 0 (buffer should start zeroed)
```

In Rust:

```rust
fn pack_portrait(is_white: impl Fn(u32, u32) -> bool, pw: u32, ph: u32) -> Vec<u8> {
    let mut out = vec![0u8; (pw * ph / 8) as usize];
    for py in 0..ph {
        for px in 0..pw {
            if is_white(px, py) {
                let bit_index = py * pw + px;
                out[(bit_index >> 3) as usize] |= 0x80 >> (bit_index & 7);
            }
        }
    }
    out
}
```

If you're going straight from a dithered/thresholded grayscale buffer, do
the thresholding (or Floyd-Steinberg dithering, if you want that quality)
*before* this step - the packer expects a clean black/white decision per
pixel, not grayscale.

## Sending a frame and reading the reply

1. Clear/reset whatever read buffer you're accumulating into.
2. Write the 9-byte header, then the payload bytes.
3. Read (accumulate) incoming bytes and watch for one of: `"DRAWING"`,
   `"OK"`, `"ERR"`.
   - Give this an initial timeout of **~10s**.
4. If you saw `"DRAWING"`, the badge has accepted the frame and started its
   e-ink refresh - keep reading and wait for `"OK"` or `"ERR"`.
   - This step takes **~15-18s** in practice; give it a generous timeout,
     **~40s**, before giving up.
5. `"ERR"` means the badge rejected/failed the frame - the original app
   just surfaces whatever text followed `"ERR"` in the buffer as a rough
   error message; there's no further structured error protocol to parse.
6. No reply within timeout = assume disconnected/hung, and reset your
   connection before retrying.

The reference implementation does **substring search** over an accumulating
buffer rather than strict message framing - the badge may interleave other
text (e.g. MicroPython banner noise) around these tokens, so don't assume
the token is the very first thing you read. Simplest robust approach in
Rust: read into a growing `String`/byte buffer on a timer or in a read loop,
and check `buf.contains("OK")` etc. after each read, same as the JS does.

## Practical notes for a long-running client

- **Only one frame in flight at a time.** There's no partial refresh and no
  queuing on the badge side - if you fire a second frame while a refresh is
  still in progress you'll desync the reply parser at best. Serialize
  writes behind a simple busy flag/mutex.
- **Full-frame refresh only.** Every update repaints the whole panel; there
  is no delta/partial-refresh protocol to talk to here even if you wanted
  one - that would be a firmware change, not a protocol one.
- Reconnect logic: if the port disappears (badge unplugged/reset), you'll
  get an OS-level I/O error on write/read - `serialport` surfaces this as an
  `Err`. Worth polling for the device (by vendor ID) and re-opening rather
  than assuming the path is stable forever, especially across a badge reset.

## Appendix: firmware install protocol (not needed for a drawing-only client)

`app.js` also has a two-step flow for flashing a fresh badge (raw MicroPython
UF2 over WebUSB bootloader mode, then pushing `einkdriver.py`/`main.py` over
a raw-REPL Ctrl-A/Ctrl-D exchange, with a `"BPNT-EXIT"` escape hatch and a
`"BPNT-READY"` boot token). You almost certainly don't need to reimplement
this in Rust unless you also want your daily-driver client to be able to
provision a brand new badge - it's a one-time setup step, not part of the
ongoing draw loop. Flagging it exists in case you ever need it; happy to
document it in the same level of detail if you do.