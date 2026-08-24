/**
 * WanderPathA Frontend API Service
 *
 * Responsible for communication between:
 *
 * React Frontend
 *        |
 *        v
 * FastAPI User Platform
 *        |
 *        v
 * AgentRouter
 *        |
 *        v
 * MCP Tools
 */


// ======================================================
// API Configuration
// ======================================================


const API_BASE_URL =
    import.meta.env.VITE_API_URL ||
    "http://localhost:8000";




// ======================================================
// Types
// ======================================================


export interface ChatRequest {

    message: string;

    session_id: string;

    customer_id?: string;

    agent_id?: string;

}



export interface ExecutionInfo {

    status: string;

    agent: string;

}



export interface ChatResponse {


    agent_id: string;


    session_id: string;


    response: string;


    execution: ExecutionInfo;

}

// ======================================================
// Agents
// ======================================================


export interface Agent {


    id: string;


    name: string;


    description: string;

}

// ======================================================
// API Error
// ======================================================


class APIError extends Error {


    status?: number;


    constructor(
        message: string,
        status?: number
    ){

        super(message);

        this.name = "APIError";

        this.status = status;

    }

}

// ======================================================
// Generic Fetch Wrapper
// ======================================================


async function apiFetch<T>(

    endpoint: string,

    options?: RequestInit

): Promise<T>{



    try {



        const response = await fetch(

            `${API_BASE_URL}${endpoint}`,

            {


                headers:{


                    "Content-Type":

                        "application/json",

                },


                ...options,

            }

        );





        if(!response.ok){


            throw new APIError(

                `API Error: ${response.status}`,

                response.status

            );

        }




        return await response.json();



    }


    catch(error){



        if(error instanceof APIError){

            throw error;

        }



        throw new APIError(

            "Backend server unavailable"

        );

    }

}


// ======================================================
// Send Chat Message
// ======================================================


export async function sendMessage(

    request: ChatRequest

): Promise<ChatResponse>{



    return apiFetch<ChatResponse>(


        "/api/chat",


        {


            method:"POST",



            body:JSON.stringify({


                message:

                    request.message,



                session_id:

                    request.session_id,



                customer_id:

                    request.customer_id || "C001",



            }),


        }


    );

}


// ======================================================
// Get Available Agents
// ======================================================


export async function getAgents()

: Promise<Agent[]>{



    return apiFetch<Agent[]>(

        "/api/agents"

    );

}

// ======================================================
// Health Check
// ======================================================


export async function healthCheck()

: Promise<boolean>{



    try{


        await apiFetch(

            "/health"

        );


        return true;


    }

    catch{


        return false;

    }

}


// ======================================================
// Mock Fallback
// Used only if backend is unavailable
// ======================================================


export function mockResponse(

    message:string,

    agent:string

):ChatResponse{


    return {


        agent_id:agent,


        session_id:"demo",


        response:


        `I received your request:
        
"${message}"

WanderPathA ${agent} is processing your request.`,



        execution:{


            status:"success",


            agent:agent,


        }

    };


}
