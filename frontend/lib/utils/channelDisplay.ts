/** Utility functions for displaying channel information. */

/**
 * Get display text for a channel.
 * @param channel - Channel identifier (e.g., "instagram", "web_chat")
 * @returns Formatted channel display string with emoji
 */
export function getChannelDisplay(channel?: string | null): string {
  if (!channel) return "-";
  if (channel === "instagram") return "📷 Instagram";
  if (channel === "telegram") return "💬 Telegram";
  if (channel === "web_chat") return "🌐 Web Chat";
  return channel;
}

/**
 * Check if a conversation is an Instagram conversation.
 * @param channel - Channel identifier
 * @returns True if channel is Instagram
 */
export function isInstagramChannel(channel?: string | null): boolean {
  return channel === "instagram";
}

/**
 * Check if a conversation is a web chat conversation.
 * @param channel - Channel identifier
 * @returns True if channel is web chat
 */
export function isWebChatChannel(channel?: string | null): boolean {
  return channel === "web_chat";
}

/**
 * Check if a conversation is a Telegram conversation.
 * @param channel - Channel identifier
 * @returns True if channel is Telegram
 */
export function isTelegramChannel(channel?: string | null): boolean {
  return channel === "telegram";
}
