import { extractVideoId } from './youtube.js';

export class ValidationError extends Error {
  constructor(msg, field) {
    super(msg);
    this.name  = 'ValidationError';
    this.field = field;
  }
}

export function validateGenerateBody(body) {
  if (!body || typeof body !== 'object') {
    throw new ValidationError('Body must be JSON', 'body');
  }
  const { url, language = 'en' } = body;
  if (typeof url !== 'string') {
    throw new ValidationError('url must be string', 'url');
  }
  const videoId = extractVideoId(url);
  if (!videoId) {
    throw new ValidationError('Invalid YouTube URL', 'url');
  }
  return { url, videoId, language };
}

export function methodOnly(reqMethod, allowed = 'POST') {
  if (reqMethod !== allowed) {
    throw new ValidationError(`Only ${allowed} allowed`, 'method');
  }
}
