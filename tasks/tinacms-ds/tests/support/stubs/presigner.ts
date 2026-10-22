// Stand-in for @aws-sdk/s3-request-presigner. Records the object key a
// presigned upload URL was minted for.

import { s3 } from './aws-s3';

export async function getSignedUrl(
  _client: any,
  command: any,
  options?: { expiresIn?: number }
): Promise<string> {
  const input = command?.input ?? {};
  s3.presigns.push({
    bucket: input.Bucket,
    key: input.Key,
    expiresIn: options?.expiresIn as number,
  });
  return `https://signed.example/${encodeURIComponent(String(input.Key))}`;
}
