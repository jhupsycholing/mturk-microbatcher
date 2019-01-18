# murk-study-manager
====
The `mTurk Study Manager` is an easy-to-use Flask application designed to streamline the process of running web experiments (Ibex experiments in particular) on the Mechanical Turk platform.

There are a number of mTurk interfaces available at the moment, but **this app will appeal to researchers interested in running web experiments that require multiple "lists"**, that is, multiple versions of the same experiment with different orderings of stimuli or different factors present.

In our HIT creation interface, you will specify the number of lists and subjects per list. Then, the app will release micro-batches of 9 or fewer subjects (which reduces the cost that mTurk takes as commission for each HIT by 50%), keeping close track of which lists have been completed at each step to ensure that the correct distribution of lists is achieved.

On top of this key feature, our app can:
  - Create HITs by specifying their parameters from scratch
  - Create HITs by copying the details from prior HITs
  - Automatically create and add subjects to Qualifications corresponding to which of your HITs they've completed
    - This is useful for whitelisting and blacklisting subjects from past experiments
  - Keep track of completed HITs and HITs in progress (e.g. subjects remaining, pending, completed, subjects per list, etc.)
  - Expire, Delete, or Approve Assignments for a given HIT
  - Switch easily between Sandbox and Mechanical Turk
  
This first release of the Study Manager is designed specifically for Ibex experiments, but it contains helper functions for custom experiments that the researcher can host directly from the server. We use the application for this purpose in our lab, and I will provide a dummy example soon that fully demonstrates this alternative functionality.
 
Installation
------------
Currently, we find it easiest to set up `mTurk Study Manager` as a Heroku application using an SQLAlchemy database. Otherwise, the user will need to use their own computer as a high-traffic server or use a service like webfactional for hosting. These options will be fleshed out soon.

First, clone this repository into a directory on your computer
      
       git clone https://github.com/jhupsycholing/mturk-ibex-study-manager.git
       
Then, create a free Heroku account and 


 
 
 
   
  



