import { convertLatexToSpeakableText } from '../../src/public/mathlive-ssr';

// The spoken form of a formula is plain text unless markup was requested. Plain
// output must stay plain: a speech engine reads the characters, not HTML entities.
function withStub(markup: '' | 'ssml', run: () => void): void {
  (globalThis as any).window = {};
  (globalThis as any).MathfieldElement = {
    createHTML: (s: string) => s,
    textToSpeechRules: '',
    textToSpeechMarkup: markup,
  };
  run();
}

describe('speakable text keeps working', () => {
  test('plain text is returned as written', () => {
    withStub('', () => {
      expect(convertLatexToSpeakableText('\\text{a&b}')).toBe('a&b');
      expect(convertLatexToSpeakableText('\\text{a<b}')).toBe('a<b');
      expect(convertLatexToSpeakableText('\\text{hello world}')).toBe(
        'hello world'
      );
    });
  });

  test('mathematical content is still spoken', () => {
    withStub('', () => {
      expect(convertLatexToSpeakableText('x')).toBe(" 'X'");
      expect(convertLatexToSpeakableText('\\frac{1}{2}').length).toBeGreaterThan(0);
    });
  });

  test('a markup document is still produced when requested', () => {
    withStub('ssml', () => {
      const output = convertLatexToSpeakableText('\\text{abc}');
      expect(output.startsWith('<?xml')).toBe(true);
      expect(output).toContain('<speak');
      expect(output).toContain('abc');
    });
  });
});
