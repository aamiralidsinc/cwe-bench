<?php
/**
 * Minimal transport interfaces for the socket server classes.
 *
 * The Ratchet server package is installed on the separate socket host, not in the web
 * application's vendored dependencies, so the application checkout does not carry it. The
 * server classes only implement these two interfaces and the harness only needs a connection
 * that records what was sent; these declarations match Ratchet's public interface.
 */
namespace Ratchet;

interface ConnectionInterface
{
    public function send($data);

    public function close();
}

interface MessageComponentInterface
{
    public function onOpen(ConnectionInterface $conn);

    public function onMessage(ConnectionInterface $from, $msg);

    public function onClose(ConnectionInterface $conn);

    public function onError(ConnectionInterface $conn, \Exception $e);
}
