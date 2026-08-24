import { useEffect, useState } from "react";

import "./index.css";

import Sidebar from "./components/Sidebar";
import ChatWindow from "./components/ChatWindow";
import MessageInput from "./components/MessageInput";
import StatusPanel from "./components/StatusPanel";

import {
    getAgents,
    sendMessage,
    AgentInfo,
    ChatExecution
} from "./api";

export interface Message {

    role: "user" | "assistant";

    content: string;
}

function App() {

    const [agents, setAgents] =
        useState<AgentInfo[]>([]);

    const [messages, setMessages] =
        useState<Message[]>([]);

    const [execution, setExecution] =
        useState<ChatExecution | null>(null);

    const [loading, setLoading] =
        useState(false);

    const sessionId = "session-001";

    const customerId = "C001";

    useEffect(() => {

        loadAgents();

    }, []);

    async function loadAgents() {

        try {

            const result =
                await getAgents();

            setAgents(result);

        } catch (err) {

            console.error(err);

        }

    }

    async function handleSend(message: string) {

        if (!message.trim()) return;

        const userMessage: Message = {

            role: "user",

            content: message

        };

        setMessages(prev => [...prev, userMessage]);

        setLoading(true);

        try {

            const response = await sendMessage({

                message,

                session_id: sessionId,

                customer_id: customerId

            });

            setMessages(prev => [

                ...prev,

                {

                    role: "assistant",

                    content: response.response

                }

            ]);

            setExecution(response.execution);

        }

        catch (err) {

            console.error(err);

            setMessages(prev => [

                ...prev,

                {

                    role: "assistant",

                    content:
                        "Something went wrong."

                }

            ]);

        }

        finally {

            setLoading(false);

        }

    }

    return (

        <div className="app">

            <Sidebar

                agents={agents}

            />

            <div className="chat-section">

                <ChatWindow

                    messages={messages}

                    loading={loading}

                />

                <MessageInput

                    onSend={handleSend}

                    disabled={loading}

                />

            </div>

            <StatusPanel

                execution={execution}

            />

        </div>

    );

}

export default App;
