import { useState } from "react";

import {
    sendMessage,
    type ChatResponse
} from "./api";



interface Message {

    role: "user" | "assistant";

    content: string;

}



const agents = [

    {
        id: "memory_agent",
        name: "Memory Agent",
        description:
            "Customer memory and preferences"
    },


    {
        id: "planning_agent",
        name: "Planning Agent",
        description:
            "Task decomposition and planning"
    },


    {
        id: "rebook_flight",
        name: "Flight Agent",
        description:
            "Flight rebooking and delays"
    },


    {
        id: "refund_with_confirmation",
        name: "Refund Agent",
        description:
            "Refund processing"
    },


    {
        id: "upgrade_to_vip",
        name: "VIP Agent",
        description:
            "VIP travel customization"
    }

];





function App() {


    const [selectedAgent,setSelectedAgent] =
        useState(
            agents[0]
        );



    const [messages,setMessages] =
        useState<Message[]>([]);



    const [input,setInput] =
        useState("");



    const [loading,setLoading] =
        useState(false);



    const [execution,setExecution] =
        useState<ChatResponse["execution"] | null>(
            null
        );





    async function handleSend(){


        if(!input.trim()) return;



        const userMessage: Message = {

            role:"user",

            content:input

        };



        setMessages(prev => [

            ...prev,

            userMessage

        ]);



        setInput("");

        setLoading(true);




        try {


            const response = await sendMessage({

                message:
                    input,


                session_id:
                    "demo",


                customer_id:
                    "C001",


                agent_id:
                    selectedAgent.id

            });





            const assistantMessage: Message = {

                role:"assistant",

                content:
                    response.response

            };



            setMessages(prev => [

                ...prev,

                assistantMessage

            ]);



            setExecution(

                response.execution

            );



        }

        catch(error){



            setMessages(prev => [


                ...prev,


                {


                    role:"assistant",


                    content:
                        "Error connecting to WanderPathA backend."


                }


            ]);

        }



        finally{


            setLoading(false);


        }

    }








    return (


        <div
            className="
            min-h-screen
            bg-slate-950
            text-white
            flex
            "
        >



            {/* Sidebar */}


            <aside
                className="
                w-72
                bg-slate-900
                border-r
                border-slate-700
                p-5
                "
            >


                <h1
                    className="
                    text-xl
                    font-bold
                    mb-6
                    "
                >

                    WanderPathA

                </h1>




                {
                    agents.map(agent => (


                        <button

                            key={agent.id}

                            onClick={() =>
                                setSelectedAgent(agent)
                            }

                            className={`
                            w-full
                            text-left
                            p-3
                            rounded
                            mb-3
                            ${
                                selectedAgent.id === agent.id
                                ?
                                "bg-purple-700"
                                :
                                "bg-slate-800"
                            }
                            `}

                        >


                            <div
                                className="
                                font-semibold
                                "
                            >

                                {agent.name}

                            </div>



                            <div
                                className="
                                text-sm
                                text-gray-300
                                "
                            >

                                {agent.description}

                            </div>


                        </button>


                    ))
                }



            </aside>








            {/* Chat Area */}


            <main
                className="
                flex-1
                flex
                flex-col
                "
            >



                <header
                    className="
                    p-5
                    border-b
                    border-slate-700
                    "
                >

                    <h2
                        className="
                        text-xl
                        "
                    >

                        {selectedAgent.name}

                    </h2>


                </header>






                <div
                    className="
                    flex-1
                    overflow-y-auto
                    p-6
                    space-y-4
                    "
                >


                    {
                        messages.map(
                            (msg,index)=>(

                                <div

                                    key={index}

                                    className={`
                                    p-4
                                    rounded-lg
                                    max-w-xl
                                    ${
                                      msg.role==="user"
                                      ?
                                      "ml-auto bg-purple-700"
                                      :
                                      "bg-slate-800"
                                    }
                                    `}

                                >

                                    {msg.content}


                                </div>


                            )
                        )
                    }





                    {
                        loading && (

                            <div
                                className="
                                bg-slate-800
                                p-4
                                rounded
                                "
                            >

                                WanderPathA is thinking...

                            </div>

                        )
                    }



                </div>









                {/* Input */}


                <div
                    className="
                    p-5
                    border-t
                    border-slate-700
                    flex
                    gap-3
                    "
                >


                    <input

                        value={input}

                        onChange={
                            e =>
                            setInput(e.target.value)
                        }

                        onKeyDown={
                            e =>
                            e.key==="Enter"
                            &&
                            handleSend()
                        }

                        className="
                        flex-1
                        bg-slate-800
                        p-3
                        rounded
                        "
                        
                        placeholder="
                        Ask WanderPathA...
                        "

                    />



                    <button

                        onClick={handleSend}

                        className="
                        bg-purple-600
                        px-6
                        rounded
                        "

                    >

                        Send

                    </button>


                </div>



            </main>








            {/* Status Panel */}


            <aside
                className="
                w-72
                bg-slate-900
                border-l
                border-slate-700
                p-5
                "
            >

                <h3
                    className="
                    font-bold
                    mb-4
                    "
                >

                    Execution Status

                </h3>



                {
                    execution ? (


                        <div>


                            <p>
                                Status:
                                {" "}
                                {execution.status}
                            </p>


                            <p>
                                Tool:
                                {" "}
                                {execution.agent}
                            </p>


                        </div>


                    )
                    :
                    (

                        <p>
                            Waiting...
                        </p>

                    )

                }


            </aside>



        </div>


    );

}



export default App;
