# **OCI Compute instances scheduler using Tagging**

This Python script will allow you to schedule your instances start up and shut down based on previously defined time slots by using the Tag Namespace feature of OCI.

The script looks for Compute instances tagged with a Schedule tag, and starts or stops the instance based on the predefined time intervals, in UTC.

>You should run this script as a cronjob for optimal results.

### **1. Adding the Tag Namespace**

Oracle Cloud Infrastructure Tagging allows you to add metadata to resources, which enables you to define keys and values and associate them with resources. You can use the tags to create a schedule for your compute instances.

### **a. Creating a Tag Namespace**

1. Open the navigation menu and click **Governance & Administration**. Under Governance, click **Tag Namespaces**.
2. A list of the tag namespaces in your current compartment is displayed.
3. Click **Create Namespace Definition**.
Enter the following:

- Create in Compartment: ``your root compartment``
- Namespace Definition Name: ``Schedule``
- Description: A friendly description. You can change this value later if you want to.
1. Click **Create Namespace Definition**.

### **b. Creating a Tag Key Definition**

1. Open the navigation menu and click **Governance & Administration**. Under Governance, click **Tag Namespaces**.
2. A list of the tag namespaces in your current compartment is displayed.
Click the tag namespace ``Schedule``.
A list of the tag key definitions that belong to the namespace is displayed.
1. Click **Create Tag Key Definition**.
Enter the following:
- Tag Key: Enter the key. The key can be up to 100 characters in length. Tag keys are case insensitive and must be unique within the tag namespace. We will create a key for each day of the week, plus some extra useful values like weekend, any day or all the days of the week:

    ``Monday``, ``Tuesday``, ``Wednesday``, ``Thursday``, ``Friday``, ``Saturday``, ``Sunday``, ``Weekday``, ``Weekend``, ``AnyDay``

- Description: Enter a friendly description.
- Cost-tracking: Leave it unchecked.
- Under Tag Value Type, choose ``Static Value``: Specifies that the user applying the tag can specify any value for this key.
4. Click **Create Tag Key Definition**.

> Repeat steps 3 - 4 for every day/ grouping of days to be added as a tag.

### **2. Tagging your Compute instances**

To apply a defined tag, you must have permission to use the namespace.

1. Open the navigation menu and click **Compute**. Under Compute, click **Instances**. A list of the instances in your current compartment is displayed. 
2. Find the instance that you want to tag, and click its name to view its details page.
3. Click **Apply Tags**. Depending on the resource, this option might appear in the More Actions menu.
4. In the Apply Tags to the Resource dialog:
- Select the Tag Namespace: ``Schedule``.
- Select the Tag Key. Example: Select ``Weekday``
- In Value, either enter a value or select one from the list. The script looks for time intervals in which the instance should be started in the format ``start time-end time``. Example: ``09:00-18:00``. You can add multiple time windows in this field, separated by ``;``. These times are UTC (server time).
5. When finished adding tags, click **Apply Tag(s)**.

### **3. OPTIONAL - Upload the script to an always-on Compute instance and create a cron job**

*Example for an Oracle Linux host:*

SSH into the instance and copy the script in ``/home/opc``.

1. Install the **Python OCI SDK**
   
   ``$ pip3 install oci``

2. Copy the **OCI config file** for the user which will be running the script in ``.oci/config``. Copy the pem key in ``.ssh``. Change the key path in the ``config`` file to the new path.

3. Create a **cron job**. In the terminal, type:

    ``$ crontab -e``

    Type ``i`` to insert a new line.

*Syntax of crontab:*

    * * * * * command to be executed
    - - - - -
    | | | | |
    | | | | ---- Day of week (0 - 7) (Sunday=0 or 7)
    | | | ------- Month (1 - 12)
    | | -------- Day of month (1 - 31)
    | ---------- Hour (0 - 23)
    ------------ Minute (0 - 59)

> You can also use a helper site such as https://crontab.guru to help you set the optimal execution times.

*Example for running the script hourly*: 

    0 * * * *   python3 /home/opc/start_stop_instances.py

2. **Save** and **close** the file (ESC, then ``:x`` or ``:wq``).
3. Check that the **cron daemon** is running and **start** it if it isn't.

    ``$ sudo systemctl status crond``

    If inactive (stopped): 

    ``$ sudo systemctl start crond``