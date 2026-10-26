// Shapes mirroring the stored in-app message and the notification payloads the product builds
// from it. Only the fields the presentation paths read are populated.

export type Destination = {
  url?: string;
  target?: unknown;
};

export type MessageParts = {
  redirect?: Destination;
  primary?: Destination & { completed?: boolean };
  secondary?: Destination & { completed?: boolean };
};

function button(type: string, content: string, destination?: Destination) {
  if (!destination) return undefined;

  return {
    type,
    content,
    url: destination.url,
    target: destination.target,
  };
}

export function makeMessageEntity(parts: MessageParts = {}): any {
  const buttons = [
    button('primary', 'Primary', parts.primary),
    button('secondary', 'Secondary', parts.secondary),
  ].filter(Boolean);

  return {
    _id: 'message-1',
    transactionId: 'transaction-1',
    content: 'notification body',
    subject: 'notification subject',
    read: false,
    seen: false,
    archived: false,
    createdAt: '2024-01-01T00:00:00.000Z',
    lastReadDate: null,
    firstSeenDate: null,
    archivedAt: null,
    channel: 'in_app',
    subscriber: {
      _id: 'subscriber-internal-1',
      subscriberId: 'subscriber-1',
      firstName: 'Sub',
      lastName: 'Scriber',
      avatar: null,
    },
    cta: {
      type: 'redirect',
      data: {
        url: parts.redirect && parts.redirect.url,
        target: parts.redirect && parts.redirect.target,
      },
      action: {
        buttons,
        status: 'pending',
        result: {},
      },
    },
    tags: ['in-app'],
    severity: 'none',
    data: {},
    template: undefined,
  };
}

export function makeTransportMessage(parts: MessageParts = {}): any {
  const buttons = [
    button('primary', 'Primary', parts.primary),
    button('secondary', 'Secondary', parts.secondary),
  ].filter(Boolean);

  return {
    _id: 'message-1',
    transactionId: 'transaction-1',
    content: 'notification body',
    subject: 'notification subject',
    read: false,
    seen: false,
    archived: false,
    createdAt: '2024-01-01T00:00:00.000Z',
    lastReadDate: null,
    firstSeenDate: null,
    archivedAt: null,
    channel: 'in_app',
    subscriber: {
      _id: 'subscriber-internal-1',
      subscriberId: 'subscriber-1',
    },
    cta: {
      data: {
        url: parts.redirect && parts.redirect.url,
        target: parts.redirect && parts.redirect.target,
      },
      action: {
        buttons,
        status: 'pending',
        result: {},
      },
    },
    tags: ['in-app'],
    severity: 'none',
    data: {},
  };
}

export function makeNotificationPayload(parts: MessageParts = {}): any {
  const action = (label: string, destination?: Destination & { completed?: boolean }) =>
    destination
      ? {
          label,
          isCompleted: !!destination.completed,
          redirect: { url: destination.url, target: destination.target },
        }
      : undefined;

  return {
    id: 'notification-1',
    transactionId: 'transaction-1',
    subject: 'notification subject',
    body: 'notification body',
    to: { id: 'subscriber-internal-1', subscriberId: 'subscriber-1' },
    isRead: false,
    isSeen: false,
    isArchived: false,
    isSnoozed: false,
    createdAt: '2024-01-01T00:00:00.000Z',
    channelType: 'in_app',
    tags: ['in-app'],
    severity: 'none',
    redirect:
      parts.redirect && parts.redirect.url
        ? { url: parts.redirect.url, target: parts.redirect.target }
        : undefined,
    primaryAction: action('Primary', parts.primary),
    secondaryAction: action('Secondary', parts.secondary),
  };
}

export function makePreviewPayload(parts: MessageParts = {}): any {
  const action = (label: string, destination?: Destination) =>
    destination
      ? { label, redirect: { url: destination.url, target: destination.target } }
      : undefined;

  return {
    id: 'notification-1',
    subject: 'notification subject',
    redirect:
      parts.redirect && parts.redirect.url
        ? { url: parts.redirect.url, target: parts.redirect.target }
        : undefined,
    primaryAction: action('Primary', parts.primary),
    secondaryAction: action('Secondary', parts.secondary),
  };
}
