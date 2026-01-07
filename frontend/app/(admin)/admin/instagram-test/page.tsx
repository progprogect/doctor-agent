"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Button } from "@/components/shared/Button";
import { Input } from "@/components/shared/Input";
import { Textarea } from "@/components/shared/Textarea";

interface LogEntry {
  timestamp: string;
  level: "info" | "success" | "error" | "warning";
  message: string;
  data?: any;
}

export default function InstagramTestPage() {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [recipientId, setRecipientId] = useState("62670099264");
  const [messageText, setMessageText] = useState("Тестовое сообщение от Doctor Agent");
  const [isSending, setIsSending] = useState(false);
  const [accountId, setAccountId] = useState("25638311079121978");
  const [recentWebhooks, setRecentWebhooks] = useState<any[]>([]);

  const addLog = (level: LogEntry["level"], message: string, data?: any) => {
    setLogs((prev) => [
      ...prev,
      {
        timestamp: new Date().toLocaleTimeString(),
        level,
        message,
        data,
      },
    ]);
  };

  const checkAccountInfo = async () => {
    try {
      addLog("info", "Проверка информации об аккаунте...");
      const response = await fetch(
        `/api/v1/instagram-test/account-info?account_id=${accountId}`
      );

      if (response.ok) {
        const data = await response.json();
        addLog("success", "Информация об аккаунте получена", data);
        return data;
      } else {
        const error = await response.json();
        addLog("error", "Ошибка получения информации", error);
      }
    } catch (error: any) {
      addLog("error", "Ошибка запроса", error.message);
    }
  };

  const sendTestMessage = async () => {
    setIsSending(true);
    addLog("info", "Начинаю отправку тестового сообщения...");
    addLog("info", `Recipient ID: ${recipientId}`);
    addLog("info", `Account ID: ${accountId}`);
    addLog("info", `Message: ${messageText}`);

    try {
      // Используем backend endpoint для отправки
      addLog("info", "Отправка через backend API...");
      const response = await fetch("/api/v1/instagram-test/send", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          account_id: accountId,
          recipient_id: recipientId,
          message_text: messageText,
          use_self_messaging: false,
        }),
      });

      const result = await response.json();
      
      if (result.success) {
        addLog("success", "✅ Сообщение успешно отправлено!", result.response_data);
      } else {
        addLog("error", `❌ Ошибка: ${result.error}`, result.response_data);
        
        // Если стандартный формат не сработал, пробуем Self Messaging
        if (result.status_code === 400 && result.response_data?.error?.code === 100) {
          addLog("info", "Пробую Self Messaging формат (без recipient)...");
          const response2 = await fetch("/api/v1/instagram-test/send", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              account_id: accountId,
              recipient_id: recipientId,
              message_text: messageText,
              use_self_messaging: true,
            }),
          });

          const result2 = await response2.json();
          if (result2.success) {
            addLog("success", "✅ Сообщение успешно отправлено через Self Messaging!", result2.response_data);
          } else {
            addLog("error", `❌ Self Messaging тоже не сработал: ${result2.error}`, result2.response_data);
          }
        }
      }
    } catch (error: any) {
      addLog("error", "Ошибка отправки", error.message);
    } finally {
      setIsSending(false);
    }
  };

  const loadRecentWebhooks = async () => {
    try {
      addLog("info", "Загрузка последних webhook событий...");
      // Загружаем реальные webhook события
      const response = await fetch("/api/v1/webhook-events/recent?limit=20");
      if (response.ok) {
        const data = await response.json();
        const events = data.events || [];
        setRecentWebhooks(events);
        addLog("success", `Загружено ${events.length} webhook событий`);
        
        // Показываем последние события в логах
        if (events.length > 0) {
          events.slice(-3).forEach((event: any) => {
            addLog("info", `📨 Webhook: ${event.type} в ${new Date(event.timestamp).toLocaleTimeString()}`, {
              sender_id: event.payload?.entry?.[0]?.messaging?.[0]?.sender?.id,
              message_text: event.payload?.entry?.[0]?.messaging?.[0]?.message?.text,
            });
          });
        }
      } else {
        addLog("error", "Ошибка загрузки webhook событий", await response.text());
      }
    } catch (error: any) {
      addLog("error", "Ошибка загрузки webhook событий", error.message);
    }
  };

  useEffect(() => {
    addLog("info", "Страница тестирования Instagram API загружена");
    loadRecentWebhooks();
    
    // Обновляем webhook события каждые 5 секунд
    const interval = setInterval(() => {
      loadRecentWebhooks();
    }, 5000);
    
    return () => clearInterval(interval);
  }, []);

  const getLogColor = (level: LogEntry["level"]) => {
    switch (level) {
      case "success":
        return "text-green-600";
      case "error":
        return "text-red-600";
      case "warning":
        return "text-yellow-600";
      default:
        return "text-gray-700";
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">
        Instagram API Тестирование
      </h1>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Левая колонка: Форма тестирования */}
        <div className="space-y-4">
          <div className="bg-white rounded-sm shadow border border-[#D4AF37]/20 p-6">
            <h2 className="text-lg font-semibold mb-4">Параметры теста</h2>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Account ID (Instagram Business Account)
                </label>
                <Input
                  value={accountId}
                  onChange={(e) => setAccountId(e.target.value)}
                  placeholder="25638311079121978"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Recipient ID (получатель)
                </label>
                <Input
                  value={recipientId}
                  onChange={(e) => setRecipientId(e.target.value)}
                  placeholder="62670099264"
                />
                <p className="text-xs text-gray-500 mt-1">
                  ID пользователя, которому отправляем сообщение
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Текст сообщения
                </label>
                <Textarea
                  value={messageText}
                  onChange={(e) => setMessageText(e.target.value)}
                  rows={3}
                  placeholder="Тестовое сообщение..."
                />
              </div>

              <div className="flex gap-2">
                <Button
                  variant="primary"
                  onClick={sendTestMessage}
                  disabled={isSending}
                >
                  {isSending ? "Отправка..." : "Отправить сообщение"}
                </Button>
                <Button variant="secondary" onClick={checkAccountInfo}>
                  Проверить аккаунт
                </Button>
                <Button variant="secondary" onClick={loadRecentWebhooks}>
                  Обновить webhooks
                </Button>
              </div>
            </div>
          </div>

          {/* Последние webhook события */}
          {recentWebhooks.length > 0 && (
            <div className="bg-white rounded-sm shadow border border-[#D4AF37]/20 p-6">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-lg font-semibold">
                  Последние webhook события ({recentWebhooks.length})
                </h2>
                <Button
                  variant="secondary"
                  onClick={async () => {
                    try {
                      const response = await fetch("/api/v1/webhook-events/clear", {
                        method: "POST",
                      });
                      if (response.ok) {
                        addLog("success", "Webhook события очищены");
                        loadRecentWebhooks();
                      }
                    } catch (error: any) {
                      addLog("error", "Ошибка очистки событий", error.message);
                    }
                  }}
                  className="text-sm"
                >
                  Очистить
                </Button>
              </div>
              <div className="space-y-2 max-h-64 overflow-y-auto">
                {recentWebhooks.slice().reverse().map((event: any, idx: number) => {
                  const messaging = event.payload?.entry?.[0]?.messaging?.[0];
                  const sender = messaging?.sender;
                  const recipient = messaging?.recipient;
                  const message = messaging?.message;
                  
                  return (
                    <div
                      key={event.id || idx}
                      className="p-3 bg-gray-50 rounded border text-sm"
                    >
                      <div className="font-medium text-xs text-gray-600 mb-1">
                        {new Date(event.timestamp).toLocaleString()}
                      </div>
                      <div className="font-medium">
                        Sender ID: {sender?.id || "N/A"}
                      </div>
                      <div className="text-xs text-gray-500">
                        Recipient ID: {recipient?.id || "N/A"}
                      </div>
                      {message?.text && (
                        <div className="mt-2 text-xs bg-white p-2 rounded">
                          <strong>Сообщение:</strong> {message.text}
                        </div>
                      )}
                      {message?.is_self && message?.is_echo && (
                        <div className="mt-1 text-xs text-blue-600 font-medium">
                          🎯 Self Messaging Event
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>

        {/* Правая колонка: Логи */}
        <div className="bg-white rounded-sm shadow border border-[#D4AF37]/20 p-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-semibold">Логи</h2>
            <Button
              variant="secondary"
              onClick={() => setLogs([])}
              className="text-sm"
            >
              Очистить
            </Button>
          </div>

          <div className="bg-gray-900 text-gray-100 p-4 rounded font-mono text-xs overflow-auto max-h-[600px]">
            {logs.length === 0 ? (
              <div className="text-gray-500">Логи появятся здесь...</div>
            ) : (
              logs.map((log, idx) => (
                <div key={idx} className="mb-2">
                  <span className="text-gray-500">[{log.timestamp}]</span>{" "}
                  <span className={getLogColor(log.level)}>
                    [{log.level.toUpperCase()}]
                  </span>{" "}
                  <span>{log.message}</span>
                  {log.data && (
                    <pre className="mt-1 ml-4 text-xs overflow-x-auto">
                      {JSON.stringify(log.data, null, 2)}
                    </pre>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Информация о документации */}
      <div className="mt-6 bg-blue-50 border border-blue-200 rounded-sm p-4">
        <h3 className="font-semibold text-blue-900 mb-2">
          📖 Информация из документации Messenger Platform
        </h3>
        <div className="text-sm text-blue-800 space-y-2">
          <p className="font-medium">Согласно документации:</p>
          <ul className="space-y-1 list-disc list-inside ml-4">
            <li>
              Instagram Messaging работает через <strong>Messenger Platform API</strong>
            </li>
            <li>
              Используется <strong>Facebook Page</strong>, связанный с Instagram Professional account
            </li>
            <li>
              <strong>24-часовое окно</strong> для ответов (можно использовать Human Agent tag для 7 дней)
            </li>
            <li>
              <strong>Self Messaging</strong>: формат БЕЗ поля recipient для отправки самому себе
            </li>
            <li>
              Сообщения от людей, которые не являются подписчиками, попадают в папку <strong>Requests</strong>
            </li>
            <li>
              Ответы через API перемещают диалог в папку <strong>General</strong>
            </li>
          </ul>
          <p className="mt-2 text-xs text-blue-600">
            <strong>Важно:</strong> С июля 2024 года доступна новая Instagram API с Instagram Login, 
            которая не требует Facebook Page. Мы используем Instagram Graph API напрямую.
          </p>
          <p className="mt-2 text-xs text-blue-600">
            <strong>Проблема:</strong> Если получаем ошибку "User not found" (код 100), 
            возможно нужно использовать Facebook Page ID вместо Instagram Account ID, 
            или проблема в 24-часовом окне ответов.
          </p>
        </div>
      </div>
    </div>
  );
}

