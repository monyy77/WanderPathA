import {
    ChatExecution
} from "../api";



interface StatusPanelProps {


    execution:

        ChatExecution | null;


}



function StatusPanel({

    execution

}:StatusPanelProps){



    return (

        <aside className="status-panel">


            <h2>

                Execution Status

            </h2>




            {

                execution ? (


                    <>


                        <div className="status-card">


                            <div className="status-title">

                                Status

                            </div>


                            <div className="status-value">

                                {execution.status}

                            </div>


                        </div>





                        <div className="status-card">


                            <div className="status-title">

                                Tool / Agent

                            </div>


                            <div className="status-value">

                                {execution.tool}

                            </div>


                        </div>



                    </>


                )

                :

                (

                    <div className="status-card">


                        Waiting for execution...


                    </div>

                )


            }



        </aside>

    );

}


export default StatusPanel;
