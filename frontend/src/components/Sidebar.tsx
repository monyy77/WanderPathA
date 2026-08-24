import { Agent } from "../api";


interface SidebarProps {

    agents: Agent[];

}



function Sidebar({

    agents

}: SidebarProps) {


    return (

        <aside className="sidebar">


            <div className="sidebar-header">

                WanderPathA

            </div>



            {

                agents.length === 0 ? (

                    <div className="sidebar-item">

                        Loading agents...

                    </div>

                )

                :

                (

                    agents.map((agent) => (

                        <div

                            key={agent.id}

                            className="sidebar-item"

                        >

                            <strong>

                                {agent.name}

                            </strong>


                            <p>

                                {agent.description}

                            </p>


                        </div>

                    ))

                )

            }


        </aside>

    );

}


export default Sidebar;
