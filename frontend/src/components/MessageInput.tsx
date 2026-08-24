import {
    useState,
    KeyboardEvent
} from "react";



interface MessageInputProps {


    onSend:

        (message:string)=>void;


    disabled:boolean;


}



function MessageInput({

    onSend,

    disabled

}:MessageInputProps){



    const [message,setMessage] =

        useState("");




    function send(){


        if(!message.trim()) return;


        onSend(message);


        setMessage("");

    }





    function handleKeyDown(

        event:KeyboardEvent<HTMLInputElement>

    ){


        if(event.key==="Enter"){


            send();


        }


    }




    return (

        <div className="message-input">


            <input


                value={message}


                onChange={

                    e=>setMessage(

                        e.target.value

                    )

                }



                onKeyDown={handleKeyDown}



                placeholder=

                    "Ask WanderPathA..."



                disabled={disabled}


            />




            <button


                onClick={send}


                disabled={disabled}


            >

                Send


            </button>



        </div>

    );

}


export default MessageInput;
