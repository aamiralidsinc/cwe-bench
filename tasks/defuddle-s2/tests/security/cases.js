'use strict';

/*
 * Hidden security cases.
 *
 * Each case drives the product's real public parsing entry point with a page (or an
 * extractor-response stub for the async paths), then re-parses the returned content and
 * asserts that no executable markup survived. The checks describe the outcome, not a
 * particular way of reaching it.
 */

const X_URL = 'https://x.com/testuser/article/123456789';
const HN_URL = 'https://news.ycombinator.com/item?id=1';
const STEAM_URL = 'https://store.steampowered.com/news/app/1';
const REDDIT_URL = 'https://old.reddit.com/r/test/comments/abc123/test_post/';
const C2_URL = 'https://wiki.c2.com/?TestPage';
const X_STATUS_URL = 'https://x.com/user/status/123456789';

function xArticleDoc(headerImg, body) {
  return `<html><head><title>Test article</title></head><body>
    <div data-testid="twitterArticleReadView">
      <div data-testid="tweetPhoto"><img ${headerImg}></div>
      <div data-testid="twitterArticleRichTextView">
        <h1 data-testid="twitter-article-title">Test article</h1>
        ${body || '<div class="public-DraftStyleDefault-block">Body text here</div>'}
      </div>
    </div></body></html>`;
}

function substackNoteDoc(meta, imageGrid) {
  return `<html><head><title>Note</title>${meta}</head><body>
    <div class="feedPermalinkUnit">
      <div class="feedCommentBody"><div class="ProseMirror FeedProseMirror"><p>Note body text here</p></div></div>
      ${imageGrid}
    </div></body></html>`;
}

function hackerNewsDoc(href) {
  return `<html><head><title>Story</title></head><body>
    <table class="fatitem">
      <tr class="athing"><td><span class="titleline"><a href='${href}'>Story</a></span></td></tr>
      <tr><td class="subtext"><span class="score">10 points</span></td></tr>
    </table></body></html>`;
}

function bbcodeDoc(body) {
  const config = JSON.stringify([{ announcement_body: { body, headline: 'Announcement' }, event_name: 'Event' }]);
  return `<html><head><title>Steam</title></head><body>
    <div id="application_config" data-partnereventstore='${config}'></div>
    <div class="content">Body</div></body></html>`;
}

function schemaDoc(text) {
  const json = JSON.stringify({ '@type': 'SocialMediaPosting', text });
  return `<html><head><title>Post</title><script type="application/ld+json">${json}</script></head>
    <body><div><p>Tiny.</p></div></body></html>`;
}

function redditDoc(flairAttribute) {
  return `<html><head><title>Post</title></head><body>
    <div class="thing link" data-author="op" data-subreddit="test"><a class="title">Post title</a>
      <div class="usertext-body"><div class="md"><p>Body text</p></div></div></div>
    <div class="commentarea"><div class="sitetable">
      <div class="thing comment" data-author="alice" data-permalink="/r/test/comments/abc123/test_post/c1/">
        <div class="entry"><div class="tagline"><span class="score unvoted">5 points</span>
          <span class="flair" ${flairAttribute}>shown</span>
          <time datetime="2024-01-02T00:00:00Z"></time></div>
          <div class="usertext-body"><div class="md"><p>Comment body</p></div></div></div>
      </div>
    </div></div></body></html>`;
}

function youtubeDoc(description) {
  const ld = JSON.stringify({
    '@type': 'VideoObject',
    name: 'Video',
    description,
    embedUrl: 'https://www.youtube.com/embed/abcdefghijk',
    uploadDate: '2024-01-01',
  });
  return `<html><head><title>Video</title><script type="application/ld+json">${ld}</script></head>
    <body><video src="https://example.test/video.mp4"></video></body></html>`;
}

function fetchReturning(body) {
  return async () => ({ ok: true, status: 200, json: async () => body, text: async () => JSON.stringify(body) });
}

function xoembedPollData(question, optionLabel) {
  return {
    tweet: {
      text: 'tweet text',
      author: { name: 'Author', screen_name: 'user' },
      article: {
        title: 'Article',
        preview_text: 'Preview',
        created_at: '2024-01-01T00:00:00Z',
        content: {
          blocks: [{ key: 'b1', text: '', type: 'atomic', inlineStyleRanges: [], entityRanges: [{ key: 0, offset: 0, length: 1 }], data: {} }],
          entityMap: [{
            key: '0',
            value: {
              type: 'POLL',
              mutability: 'Mutable',
              data: { question, options: [{ label: optionLabel }, { label: 'Plain option' }] },
            },
          }],
        },
        media_entities: [],
      },
    },
  };
}

module.exports = function (ctx) {
  const { Defuddle, DefuddleClass, makeDoc, assertNoExecutable } = ctx;
  const parse = (html, url) => new DefuddleClass(makeDoc(html, url), { url }).parse();

  return [
    {
      classname: 'security',
      name: 'x-article-header-alt',
      run() {
        const html = xArticleDoc(`src="https://example.test/image.jpg" alt='screenshot" onerror="alert(1)'`);
        assertNoExecutable(parse(html, X_URL).content);
      },
    },
    {
      classname: 'security',
      name: 'x-article-header-src',
      run() {
        const html = xArticleDoc('src="javascript:alert(1)" alt="screenshot"');
        assertNoExecutable(parse(html, X_URL).content);
      },
    },
    {
      classname: 'security',
      name: 'substack-note-image',
      run() {
        const html = substackNoteDoc(
          `<meta property="og:image" content='https://example.test/image.jpg" onerror="alert(1)'>`,
          '<div class="imageGrid"></div>'
        );
        assertNoExecutable(parse(html, 'https://substack.com/@user/note/c-123').content);
      },
    },
    {
      classname: 'security',
      name: 'youtube-description',
      run() {
        const html = youtubeDoc('Hello <img src=x onerror=alert(1)> world');
        assertNoExecutable(parse(html, 'https://www.youtube.com/watch?v=abcdefghijk').content);
      },
    },
    {
      classname: 'security',
      name: 'schema-text-fallback',
      run() {
        const text = 'Safe intro words words words words words words words words words words words words '
          + 'words words words words words words words words words words '
          + '<img src=x onerror=alert(1)> <object data="https://example.test/x"></object> '
          + 'more padding words words words words words words words words words words words words '
          + 'words words words words words words words words words words words words words';
        assertNoExecutable(parse(schemaDoc(text), 'https://example.test/post').content);
      },
    },
    {
      classname: 'security',
      name: 'hackernews-post-link',
      run() {
        assertNoExecutable(parse(hackerNewsDoc('https://example.test/x" onmouseover="alert(1)'), HN_URL).content);
      },
    },
    {
      classname: 'security',
      name: 'bbcode-image',
      run() {
        assertNoExecutable(parse(bbcodeDoc('[img]https://example.test/image.jpg" onerror="alert(1)[/img]'), STEAM_URL).content);
      },
    },
    {
      classname: 'security',
      name: 'x-oembed-poll',
      async run() {
        const doc = makeDoc('<html><head><title>X</title></head><body></body></html>', X_STATUS_URL);
        const response = await Defuddle(doc, X_STATUS_URL, {
          fetch: fetchReturning(xoembedPollData('Best <img src=x onerror=alert(1)> option?', 'A<img src=y onerror=alert(2)>')),
        });
        assertNoExecutable(response.content);
      },
    },
    {
      classname: 'security',
      name: 'reddit-comment-flair',
      run() {
        assertNoExecutable(parse(redditDoc(`title='<img src=x onerror=alert(1)>'`), REDDIT_URL).content);
      },
    },
    {
      classname: 'security',
      name: 'c2-wiki-link-text',
      async run() {
        const doc = makeDoc('<html><head><title>C2</title></head><body></body></html>', C2_URL);
        const response = await Defuddle(doc, C2_URL, {
          fetch: fetchReturning({ text: 'Hello [[<img src=x onerror=alert(1)>]] and [[FrontPage]] end', date: '2024-01-01' }),
        });
        assertNoExecutable(response.content);
      },
    },
  ];
};
