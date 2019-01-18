# mturk-ibex-study-manager
The mTurk Ibex Study Manager is an easy-to-us Flask application designed to streamline the process of running web experiments (Ibex experiments in particular) on the Mechanical Turk platform.

There are a number of mTurk interfaces available at the moment, but this app will appeal to researchers interested in running web experiments that require multiple "lists", that is, multiple versions of the same experiment with different orderings of stimuli or different factors present.

Without our study manager, a researcher may have to manually run all their lists in order, making sure to blacklist all subjects from prior lists when each new batch is released. They also may have been using IbexFarm's built in system for list randomization, which is extremely basic (by their own admission) and often results in significantly imbalanced lists.

In our HIT creation interface, you will simply specify the number of lists and subjects per list in general or specify the exact number of subjects to run for each particular list. Then, the app will release micro-batches of 9 or fewer subjects (which reduces the cost that mTurk takes as commission for each HIT by 50%, saving money), keeping close track of which lists have been completed at each step to ensure that the correct distribution of lists is achieved.

On top of this key feature, our app can:
  - Create HITs by specifying their parameters from scratch
  - Create HITs by copying the details from prior HITs
  - Automatically create and add subjects to Qualifications corresponding to which of your HITs they've completed
    - This is useful for whitelisting and blacklisting subjects from past experiments
  - Keep track of completed HITs and HITs in progress (e.g. subjects remaining, pending, completed, subjects per list, etc.)
  - Expire, Delete, or Approve Assignments for a given HIT
  - Switch easily between Sandbox and Mechanical Turk
  
 This first release of the Study Manager is designed specifically for Ibex experiments, but it contains helper functions for custom experiments that the researcher can host directly from the server. We use the application for this purpose in our lab, and I will provide a dummy example soon that fully demonstrates this alternative functionality.
 
 
   
  



