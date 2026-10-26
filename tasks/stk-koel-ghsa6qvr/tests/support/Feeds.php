<?php

namespace Tests\Hidden;

/**
 * Minimal podcast feeds whose media URLs are IP literals, so the fixtures never depend on name
 * resolution.
 */
final class Feeds
{
    public static function one(string $enclosureUrl): string
    {
        return <<<XML
            <?xml version="1.0" encoding="UTF-8"?>
            <rss version="2.0">
                <channel>
                    <title>Hidden Test Podcast</title>
                    <link>https://8.8.8.8</link>
                    <description>A podcast used by the hidden test suite.</description>
                    <language>en-US</language>
                    <item>
                        <title>Episode One</title>
                        <description>The first episode.</description>
                        <enclosure length="1000" type="audio/mpeg" url="{$enclosureUrl}" />
                        <guid>hidden-episode-1</guid>
                        <pubDate>Tue, 8 Jan 2019 01:15:00 GMT</pubDate>
                    </item>
                </channel>
            </rss>
            XML;
    }

    public static function mixed(string $publicUrl, string $internalUrl): string
    {
        return <<<XML
            <?xml version="1.0" encoding="UTF-8"?>
            <rss version="2.0">
                <channel>
                    <title>Hidden Mixed Podcast</title>
                    <link>https://8.8.8.8</link>
                    <description>A podcast mixing safe and unsafe media URLs.</description>
                    <language>en-US</language>
                    <item>
                        <title>Episode Public</title>
                        <description>A public episode.</description>
                        <enclosure length="1000" type="audio/mpeg" url="{$publicUrl}" />
                        <guid>hidden-public-1</guid>
                        <pubDate>Tue, 8 Jan 2019 01:15:00 GMT</pubDate>
                    </item>
                    <item>
                        <title>Episode Internal</title>
                        <description>An episode pointing at a host only the server can reach.</description>
                        <enclosure length="1000" type="audio/mpeg" url="{$internalUrl}" />
                        <guid>hidden-internal-1</guid>
                        <pubDate>Tue, 8 Jan 2019 01:15:00 GMT</pubDate>
                    </item>
                </channel>
            </rss>
            XML;
    }
}
