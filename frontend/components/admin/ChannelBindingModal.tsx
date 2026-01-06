/** Modal for creating channel bindings. */

"use client";

import { useState } from "react";
import { api, ApiError } from "@/lib/api";
import { Button } from "@/components/shared/Button";
import { Input } from "@/components/shared/Input";
import type { ChannelType, CreateChannelBindingRequest } from "@/lib/types/channel";

interface ChannelBindingModalProps {
  agentId: string;
  channelType: ChannelType;
  onClose: () => void;
  onSuccess: () => void;
}

export function ChannelBindingModal({
  agentId,
  channelType,
  onClose,
  onSuccess,
}: ChannelBindingModalProps) {
  const [formData, setFormData] = useState<CreateChannelBindingRequest>({
    channel_type: channelType,
    channel_account_id: "",
    access_token: "",
    channel_username: "",
    metadata: {},
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      await api.createChannelBinding(agentId, formData);
      onSuccess();
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Failed to create channel binding");
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    const { name, value } = e.target;
    if (name === "channel_account_id" || name === "access_token" || name === "channel_username") {
      setFormData({ ...formData, [name]: value });
    } else if (name === "app_id" || name === "app_secret") {
      setFormData({
        ...formData,
        metadata: { ...formData.metadata, [name]: value },
      });
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-sm shadow-lg max-w-md w-full mx-4 p-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4">
          Connect {channelType === "instagram" ? "Instagram" : channelType} Account
        </h2>

        {error && (
          <div className="bg-red-50 border-l-4 border-red-500 p-4 mb-4 rounded-sm">
            <p className="text-sm text-red-700">{error}</p>
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="space-y-4">
            <Input
              label="Instagram Account ID"
              name="channel_account_id"
              value={formData.channel_account_id}
              onChange={handleChange}
              required
              placeholder="17841458318357324"
            />

            <Input
              label="Access Token"
              name="access_token"
              type="password"
              value={formData.access_token}
              onChange={handleChange}
              required
              placeholder="IGAAXjRiKjwKFBZAGFRU1RTcUdhU1UwYWhvTndCdWJNSEFGN1FEZA1M5N0Rhekp3MDE4NUpKanlwd1haSHpubmRFZAk8xbXF1UF9CRmRZATHRqWU44QURYVlcwZA2VhaVV1MngwYUdSeDRXVTdEcWhCNmhpLTR2S3NrRWxzQU5UcEQ5dwZDZD"
            />

            <Input
              label="Instagram Username (optional)"
              name="channel_username"
              value={formData.channel_username || ""}
              onChange={handleChange}
              placeholder="@username"
            />

            <Input
              label="App ID (optional)"
              name="app_id"
              value={formData.metadata?.app_id || ""}
              onChange={handleChange}
              placeholder="1657265251926177"
            />

            <Input
              label="App Secret (optional)"
              name="app_secret"
              type="password"
              value={formData.metadata?.app_secret || ""}
              onChange={handleChange}
              placeholder="8009196538c78a40e3f8b79a8ddcc536"
            />
          </div>

          <div className="flex justify-end gap-2 mt-6">
            <Button type="button" variant="secondary" onClick={onClose}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" disabled={isSubmitting}>
              {isSubmitting ? "Connecting..." : "Connect"}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}

