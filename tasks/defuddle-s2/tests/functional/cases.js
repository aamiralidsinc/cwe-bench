'use strict';

/*
 * Hidden functional cases.
 *
 * These drive the same public parsing entry points as the security cases and assert that
 * legitimate behaviour — ordinary text and attribute values, media embeds, relative-address
 * resolution, and each page shape's visible content — is unchanged.
 */

const fs = require('fs');
const path = require('path');

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
      <tr class="athing"><td><span class="titleline"><a href="${href}">Story</a></span></td></tr>
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

function youtubeDoc(description, transcript) {
  const ld = JSON.stringify({
    '@type': 'VideoObject',
    name: 'Video',
    description,
    embedUrl: 'https://www.youtube.com/embed/abcdefghijk',
    uploadDate: '2024-01-01',
  });
  const transcriptHtml = transcript
    ? `<ytd-engagement-panel-section-list-renderer target-id="engagement-panel-searchable-transcript">
        <div id="segments-container">
          <ytd-transcript-segment-renderer><div class="segment-timestamp">0:01</div><div class="segment-text">hello there</div></ytd-transcript-segment-renderer>
        </div>
      </ytd-engagement-panel-section-list-renderer>`
    : '';
  return `<html><head><title>Video</title><script type="application/ld+json">${ld}</script></head>
    <body><video src="https://example.test/video.mp4"></video>${transcriptHtml}</body></html>`;
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
  const { Defuddle, DefuddleClass, makeDoc, harness, WORKSPACE } = ctx;
  const { attr, hasElement } = harness;
  const parse = (html, url) => new DefuddleClass(makeDoc(html, url), { url }).parse();

  return [
    {
      classname: 'functional',
      name: 'x-article-header-preserved',
      async run() {
        const alt = 'A fine & <sharp> caption';
        const html = xArticleDoc(
          `src="https://example.test/image.jpg" alt='${alt}'`,
          '<div class="public-DraftStyleDefault-block">Body <a href="/relative/page">relative link</a></div>'
        );
        const result = parse(html, X_URL);
        if (attr(result.content, 'img', 'alt') !== alt) {
          throw new Error('the header image alt value was not preserved');
        }
        const src = attr(result.content, 'img', 'src');
        if (!src || !src.startsWith('https://example.test/image.jpg')) {
          throw new Error('the header image address was not preserved: ' + src);
        }
        const href = attr(result.content, 'a', 'href');
        if (href !== 'https://x.com/relative/page') {
          throw new Error('relative link was not resolved against the page address: ' + href);
        }
      },
    },
    {
      classname: 'functional',
      name: 'x-article-body-text',
      async run() {
        const body = '<div class="public-DraftStyleDefault-block">Keep 3 &lt; 5 &amp; "quotes" — naïve café</div>';
        const result = parse(xArticleDoc('src="https://example.test/image.jpg" alt="ok"', body), X_URL);
        for (const phrase of ['Keep 3', 'quotes', 'naïve café']) {
          if (!result.content.includes(phrase)) throw new Error('body text was not preserved: ' + phrase);
        }
      },
    },
    {
      classname: 'functional',
      name: 'substack-note-image-preserved',
      async run() {
        const html = substackNoteDoc(
          '',
          '<div class="imageGrid"><img srcset="https://cdn.test/small.jpg 100w, https://cdn.test/large.jpg 800w"></div>'
        );
        const result = parse(html, 'https://substack.com/@user/note/c-123');
        if (!result.content.includes('https://cdn.test/large.jpg')) {
          throw new Error('the note image was not preserved');
        }
        if (!result.content.includes('Note body text here')) {
          throw new Error('the note text was not preserved');
        }
      },
    },
    {
      classname: 'functional',
      name: 'youtube-embed-preserved',
      async run() {
        const result = parse(youtubeDoc('Line one\nLine two'), 'https://www.youtube.com/watch?v=abcdefghijk');
        if (!hasElement(result.content, 'iframe')) throw new Error('the video embed was removed');
        const src = attr(result.content, 'iframe', 'src');
        if (src !== 'https://www.youtube.com/embed/abcdefghijk') {
          throw new Error('the video embed address changed: ' + src);
        }
        if (!result.content.includes('Line one') || !result.content.includes('Line two')) {
          throw new Error('the description was not preserved');
        }
        if (!result.content.includes('<br>')) throw new Error('description line breaks were not preserved');
      },
    },
    {
      classname: 'functional',
      name: 'youtube-transcript-preserved',
      async run() {
        const result = parse(youtubeDoc('Plain description', true), 'https://www.youtube.com/watch?v=abcdefghijk');
        if (!result.content.includes('hello there')) throw new Error('the transcript was not preserved');
      },
    },
    {
      classname: 'functional',
      name: 'schema-text-fallback-preserved',
      async run() {
        const text = 'This unique schema text does not appear anywhere in the visible DOM body content. '
          + 'It has enough words to trigger the fallback path. We need quite a few words here to exceed '
          + 'the extracted content word count. Adding more sentences to be safe and ensure we trigger the right code path.';
        const result = parse(schemaDoc(text), 'https://example.test/post');
        if (!result.content.includes('unique schema text')) throw new Error('schema text fallback content was lost');
        if (!result.content.includes('right code path')) throw new Error('schema text fallback content was truncated');
      },
    },
    {
      classname: 'functional',
      name: 'schema-matched-element-preserved',
      async run() {
        const plainText = 'This post has formatted content with bold text and italic text and a link to example site. '
          + 'It needs enough words to trigger the schema fallback path so we keep adding more content here.';
        const json = JSON.stringify({ '@type': 'SocialMediaPosting', text: plainText });
        const html = `<html><head><title>Post</title><script type="application/ld+json">${json}</script></head><body>
          <div><p>Nav item</p></div>
          <div class="post"><p>This post has <strong>formatted content</strong> with <em>bold text</em> and
          <a href="https://example.test/link">link to example site</a>. It needs enough words to trigger the
          schema fallback path so we keep adding more content here.</p></div></body></html>`;
        const result = parse(html, 'https://example.test/post');
        if (!result.content.includes('<strong>formatted content</strong>')) {
          throw new Error('inline formatting in matched schema content was lost');
        }
        if (!result.content.includes('https://example.test/link')) {
          throw new Error('the matched schema content link was lost');
        }
      },
    },
    {
      classname: 'functional',
      name: 'hackernews-link-preserved',
      async run() {
        const result = parse(hackerNewsDoc('https://example.test/story'), HN_URL);
        if (attr(result.content, 'a', 'href') !== 'https://example.test/story') {
          throw new Error('the story link was not preserved');
        }
        if (result.title !== 'Story') throw new Error('the story title was not preserved: ' + result.title);
      },
    },
    {
      classname: 'functional',
      name: 'bbcode-conversion-preserved',
      async run() {
        const result = parse(bbcodeDoc('[img]https://example.test/image.png[/img] [url=https://example.test/page]page[/url]'), STEAM_URL);
        if (!result.content.includes('https://example.test/image.png')) throw new Error('the converted image was lost');
        if (!result.content.includes('https://example.test/page')) throw new Error('the converted link was lost');
        if (!result.content.includes('page')) throw new Error('the link text was lost');
      },
    },
    {
      classname: 'functional',
      name: 'x-oembed-poll-preserved',
      async run() {
        const doc = makeDoc('<html><head><title>X</title></head><body></body></html>', X_STATUS_URL);
        const response = await Defuddle(doc, X_STATUS_URL, {
          fetch: fetchReturning(xoembedPollData('Best option?', 'Option A')),
        });
        for (const phrase of ['Best option?', 'Option A', 'Plain option']) {
          if (!response.content.includes(phrase)) throw new Error('poll content was lost: ' + phrase);
        }
        if (!hasElement(response.content, 'div.poll')) throw new Error('the poll block was removed');
      },
    },
    {
      classname: 'functional',
      name: 'reddit-comment-metadata-preserved',
      async run() {
        const result = parse(redditDoc(`title='Top contributor'`), REDDIT_URL);
        if (!result.content.includes('Top contributor')) throw new Error('comment flair was lost');
        if (!result.content.includes('alice')) throw new Error('comment author was lost');
        if (!result.content.includes('Comment body')) throw new Error('comment body was lost');
      },
    },
    {
      classname: 'functional',
      name: 'c2-wiki-link-preserved',
      async run() {
        const doc = makeDoc('<html><head><title>C2</title></head><body></body></html>', C2_URL);
        const response = await Defuddle(doc, C2_URL, {
          fetch: fetchReturning({ text: 'See [[FrontPage]] for details', date: '2024-01-01' }),
        });
        if (!response.content.includes('https://wiki.c2.com/?FrontPage')) throw new Error('the wiki link address was lost');
        if (!response.content.includes('FrontPage')) throw new Error('the wiki link text was lost');
      },
    },
    {
      classname: 'functional',
      name: 'plain-article-content',
      async run() {
        const html = `<html><head><title>Plain</title></head><body><article>
          <h1>Plain article</h1>
          <p>An ordinary paragraph with ordinary words and an <a href="/more">ordinary link</a>.</p>
          <iframe src="https://player.example.test/embed/1" width="560" height="315"></iframe>
          </article></body></html>`;
        const result = parse(html, 'https://example.test/plain');
        for (const phrase of ['Plain article', 'ordinary paragraph']) {
          if (!result.content.includes(phrase)) throw new Error('page content was lost: ' + phrase);
        }
        if (!hasElement(result.content, 'iframe')) throw new Error('an ordinary media embed was removed');
        if (attr(result.content, 'a', 'href') !== 'https://example.test/more') {
          throw new Error('the ordinary link was not resolved');
        }
      },
    },
    {
      classname: 'functional',
      name: 'project-x-article-fixture',
      async run() {
        const file = path.join(WORKSPACE, 'tests', 'fixtures', 'general--x.com-article-2026-02-13.html');
        const html = fs.readFileSync(file, 'utf8');
        const result = parse(html, 'https://x.com/Heinrich/article/2011686615994220679');
        if (result.title !== 'obsidian + claude code 101') {
          throw new Error('the fixture title changed: ' + result.title);
        }
        if (!result.content.includes('operating system for thinking')) {
          throw new Error('the fixture article body was lost');
        }
      },
    },
  ];
};
