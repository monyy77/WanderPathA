import { Message } from "../App";


interface ChatWindowProps {


    messages: Message[];


    loading: boolean;


}



function ChatWindow({

    messages,

    loading

}: ChatWindowProps) {



    if(messages.length === 0){


        return (

            <div className="chat-window">

                <div className="empty-chat">

                    Start conversation with WanderPathA AI Agent

                </div>

            </div>

        );

    }




    return (

        <div className="chat-window">


            {

                messages.map((message,index)=>(


                    <div

                        key={index}

                        className={

                            `message ${message.role}`

                        }

                    >

                        {message.content}


                    </div>


                ))

            }




            {

                loading && (

                    <div className="message assistant">

                        Thinking...

                    </div>

                )

            }



        </div>

    );

}



export default ChatWindow;
