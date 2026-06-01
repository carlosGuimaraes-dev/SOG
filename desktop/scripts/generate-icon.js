const fs = require('node:fs')
const path = require('node:path')
const zlib = require('node:zlib')

const size = 512
const outDir = path.resolve(__dirname, '..', 'build')
const outPath = path.join(outDir, 'icon.png')

function crc32(buffer) {
  let crc = 0xffffffff
  for (const byte of buffer) {
    crc ^= byte
    for (let i = 0; i < 8; i += 1) {
      crc = (crc >>> 1) ^ (0xedb88320 & -(crc & 1))
    }
  }
  return (crc ^ 0xffffffff) >>> 0
}

function chunk(type, data) {
  const typeBuffer = Buffer.from(type)
  const length = Buffer.alloc(4)
  length.writeUInt32BE(data.length)
  const crc = Buffer.alloc(4)
  crc.writeUInt32BE(crc32(Buffer.concat([typeBuffer, data])))
  return Buffer.concat([length, typeBuffer, data, crc])
}

function pixel(x, y) {
  const cx = x - size / 2
  const cy = y - size / 2
  const distance = Math.sqrt(cx * cx + cy * cy) / (size / 2)
  const inBadge = distance < 0.82
  const barA = Math.abs(y - (size * 0.38 + x * 0.08)) < 34 && x > 125 && x < 390
  const barB = Math.abs(y - (size * 0.52 - x * 0.05)) < 30 && x > 120 && x < 395
  const barC = Math.abs(y - (size * 0.66 + x * 0.06)) < 28 && x > 135 && x < 375

  if (barA || barB || barC) return [245, 250, 252, 255]
  if (inBadge) {
    const shade = Math.max(0, 1 - distance)
    return [
      Math.round(35 + shade * 42),
      Math.round(95 + shade * 90),
      Math.round(125 + shade * 82),
      255,
    ]
  }
  return [14, 20, 26, 0]
}

const raw = Buffer.alloc((size * 4 + 1) * size)
let offset = 0
for (let y = 0; y < size; y += 1) {
  raw[offset] = 0
  offset += 1
  for (let x = 0; x < size; x += 1) {
    const [r, g, b, a] = pixel(x, y)
    raw[offset] = r
    raw[offset + 1] = g
    raw[offset + 2] = b
    raw[offset + 3] = a
    offset += 4
  }
}

const ihdr = Buffer.alloc(13)
ihdr.writeUInt32BE(size, 0)
ihdr.writeUInt32BE(size, 4)
ihdr[8] = 8
ihdr[9] = 6
ihdr[10] = 0
ihdr[11] = 0
ihdr[12] = 0

fs.mkdirSync(outDir, { recursive: true })
fs.writeFileSync(outPath, Buffer.concat([
  Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]),
  chunk('IHDR', ihdr),
  chunk('IDAT', zlib.deflateSync(raw, { level: 9 })),
  chunk('IEND', Buffer.alloc(0)),
]))

console.log(`icon=${outPath}`)
