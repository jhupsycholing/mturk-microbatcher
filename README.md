# mTurk-Ibex-Study-Manager

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

**This application was developed by Brian Leonard (bleona10@jhu.edu) in his capacity as Lab Manager of the JHU Computation and Psycholinguistics Lab (http://jhpsycholing.webfactional.com/), which is overseen by Dr. Tal Linzen (http://tallinzen.net)**
 
## Installation

Currently, we find it easiest to set up `mTurk Study Manager` as a Heroku application using an SQLAlchemy database. Otherwise, the user will need to use their own computer as a high-traffic server or use a service like webfactional for hosting. These options will be fleshed out soon.

First, clone this repository into a directory on your computer
      
       git clone https://github.com/jhupsycholing/mturk-ibex-study-manager.git
       
Then, create a free Heroku account if you don't already have one and select 'Create New App' once you've logged in.

For 'Deployment Method', we'll be using the Heroku CLI, which you should download and install from [here][https://devcenter.heroku.com/articles/heroku-command-line]

Make sure that you're logged in with the CLI by typing

        heroku login
        
in the terminal/console and entering your account credentials. Then, you just need to add the heroku remote from within the directory you cloned into:

        heroku git:remote -a [the name of your application]
        
Now, you can deploy your application with these three steps

        git add .
        git commit -m 'first commit'
        git push heroku master
        

        
## Configuration
        
The final step will be to fill in your app's config file with the necessary credentials to interface with your Amazon Web Services account and your SQLAlchemy database.

Inside the 'appconfig.cfg' file, which is found in the 'app' directory, you will find a template ready to fill out. For your `AWS_ACCESS_KEY` and `AWS_SECRET_ACCESS_KEY`, if you don't know how to find these, you can follow [this simple guide][https://help.bittitan.com/hc/en-us/articles/115008255268-How-do-I-find-my-AWS-Access-Key-and-Secret-Access-Key-]. 

For your `SQLALCHEMY_DATABASE_URI`, you can find this by logging into heroku.com, navigating to the homepage for the app you've created, and checking the 'Installed Add-ons' section. If there's an add-on called 'Heroku Postgres', then click this. Otherwise click 'Configure Add-ons' and search 'postgres' to add a database. Once you've clicked on your postgres database, navigate to 'Settings' and click 'View Credentials'. Copy the field labeled 'URI' into your config file as `SQLALCHEMY_DATABASE_URI`.

You will also need to input your app's name (exactly as it appears) for the `APP_NAME` field, and you should provide a personalized password in the `PASSWORD` field, which you will use to authorize actions while using the app.

The `SANDBOX` variable has True as its default value. This means all the HITs you create will appear on Mechanical Turk Sandbox, where users can test out HITs for free in order to prepare them to be released in earnest. When you are ready to leave sandbox mode, change the `SANDBOX` variable to False.

## Usage

You will use your web browser to interface with the `mTurk Study Manager`. There are a number of pages you can visit to access the features of the application, once running on heroku.

Before using the app, you should set up your database by visiting `https://[your-app-name].herokuapp.com/dropTables`



### Create HITs

To create a HIT, visit this URL: `https://[your-app-name].herokuapp.com/createHIT`

Once there you'll be presented with an html form that includes everything you need to configure your first experiment:
  - **An option to select a previous HIT that you have run**, which will then fill most of the details needed automatically
  - **The URL for the Ibex experiment you're running**. If something other than an Ibex URL is entered here, the `mTurk Study Manager` will assume you are running a custom web experiment with your own HTML and JS set up
  - **The Title of the HIT** *
  - **A Description of the HIT**
  - **Some Keywords to help turkers find the HIT** (separated by comma)
  - **The Maximum Duration of your Experiment** (in minutes) -- This means that any turker who hasn't completed the HIT within this time limit will be automatically rejected. It is important to have a time limit so turkers can't accept the HIT and hold onto it as long as they want. Think of a good estimate for the duration of your experiment, then add 50% to that amount. This is probably a safe and fair Maximum Duration.
  - **Duration of the HIT** (in days) -- This is how long the HIT will stay open for turkers to accept. 2 days is the default in our app and a reasonable choice. If you have a reason to, adjust this to your liking.
  - **Reward for the HIT** (in dollars, e.g. 2, 2.50, etc.) -- This is how much you'll pay out for every turker you approve. Amazon will add a 20% commission to this amount. 
  - **Will the HIT require Masters?** -- Certain experienced turkers have a special qualification called 'Masters', which indicates their experience and reliability, and incurs an additional charge. 
  - **Will the HIT require the turker to live in the US?** -- This qualification makes sure that the turker has a US address on file, a crude method for increasing the likelihood of a native English-speaking turker.
  - **How many lifetime HITs approved must a turker have?** -- This can be used if you want to ensure that your subjects are experienced to a certain degree with Mechanical Turk. Leave blank if not interested.
  - **Groups Excluded from HIT** -- Select one your own qualifications to exclude from your subject pool. *
  - **Groups Included in HIT** -- Select one of your own qualifications that you would like all of your subjects to possess
  - **Ibex End-Of-Experiment Code** (CASE SENSITIVE) -- This is a survey code that you will embed at the end of your Ibex experiment, so that turkers can verify that they completed it.
  - **Account Password** -- type in the `PASSWORD` from your config file to validate the createHIT action
  - **Number of Lists** -- How many lists are available in your Ibex Experiment?
  - **Equal number of subjects?** -- Will you have the same number of subjects for each list? If yes, indicate how many. If no, indicate the amount of subjects for each individual list
  
  
*It should be noted that `mTurk Study Manager` uses HIT titles to keep track of past experiments. Whenever a subject completes a HIT, they will become associated with two qualifications. One will have the same name as the title of the HIT, indicating that they have completed a HIT with this Title. If you use consistent titles for different Ibex experiments you're running, you can add this qualification to the 'Excluded' list to blacklist anyone who has completed that experiment before. The other qualification is used to keep track of subjects across a series of micro-batched HITs (which is how all HITs are distributed with this app). The name of this qualification is in the form '{HIT Title} -- {HITId}', where HITId corresponds to the ID for the first micro-batch in the series.

  
### Review HITs

Once a HIT has been successfully created, you can track its progress by visiting `https://[your-app-name].herokuapp.com/reviewHITs`

From this page, you can see how many Assignments (subjects) are pending or completed, as well as how many subjects have submitted for each list.

If you enter your `PASSWORD` at the top of the page, you can expire, delete, or approve all assignments for a given HIT (that is, Group of micro-batched HITs). We will be adding the ability to approve and reject and award bonuses to individual workers soon.

### Reset Database

If for any reason you need to reset your database and clear your tables (make sure you approve all outstanding assignments before doing this), you can visit `https://[your-app-name].herokuapp.com/dropTables`
  
  
--------------
  
 **IMPORTANT SECURITY NOTICE** -- It is safe to push applications containing sensitive AWS credentials to heroku applications and the heroku repositories that host them, but be careful to never push a config file with AWS credentials to a public github repository for any reason. It will compromise the security of your account.
  
  



