// Tiny valid PNG (1x1 transparent pixel). Real iris bytes are not needed
// because backend interactions are mocked at the network layer.
export const TINY_PNG = Buffer.from(
  'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVQI12P4//8/AwAI/AL+Q4n4VgAAAABJRU5ErkJggg==',
  'base64',
)

export const FIXTURE_PNG = {
  name: 'iris.png',
  mimeType: 'image/png',
  buffer: TINY_PNG,
}
