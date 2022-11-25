# Copyright 2021 Oracle
# Liana Lixandru

import oci
import datetime
import time
import calendar
import argparse

# Find all instances in a tenancy/compartment


def find_list_of_tagged_instances(compartment, region):
    search_client = oci.resource_search.ResourceSearchClient(config)
    print('RQS search to find instances')
    try:
        search_client.base_client.set_region(region)
        structured_search = oci.resource_search.models.StructuredSearchDetails(
            query="query instance resources",
            type='Structured',
            matching_context_type=oci.resource_search.models.SearchDetails.MATCHING_CONTEXT_TYPE_NONE)
        results = search_client.search_resources(structured_search)
    except oci.exceptions.ServiceError as e:
        print('\t\tRQS Search failed with Service Error: {0}' .format(e))
    except oci.exceptions.RequestException as e:
        print('\t\tRQS Search failed w/ a Request exception. {0}' .format(e))
    filter_key = 'Schedule'
    instances = []
    if compartment:
        for result in results.data.items:
            if result.compartment_id == compartment:
                if (filter_key in str(result.defined_tags)):
                    if result.lifecycle_state.upper() not in "TERMINATED":
                        instances.append(result)
        return instances
    else:
        return results.data.items


# Start instance


def start_instance(instance_id):
    try:
        if base_compute.get_instance(instance_id).data.lifecycle_state in 'STOPPED':
            try:
                print('\t\tStarting instance {0}.  Start response code: {1}'
                      .format(instance_id, str(base_compute.instance_action(instance_id, 'start').status)))
            except oci.exceptions.ServiceError as e:
                print('\t\tStarting instance failed. {0}' .format(e))
    except oci.exceptions.ServiceError as e:
        print('\t\tStarting instance failed. {0}'.format(e))
    return


# Stop instance


def stop_instance(instance_id):
    try:
        if base_compute.get_instance(instance_id).data.lifecycle_state in 'RUNNING':
            try:
                print('\t\tStopping instance {0}.  Stop response code: {1}'
                      .format(instance_id, str(base_compute.instance_action(instance_id, 'stop').status)))
            except oci.exceptions.ServiceError as e:
                print('\t\tStopping instance failed. {0}' .format(e))
    except oci.exceptions.ServiceError as e:
        print('\t\tStopping instance failed. {0}'.format(e))
    return

# Parse tags to create schedule object


def parse_tags(instance_list):
    result = []
    for instance in instance_list:
        if ('Schedule' in str(instance.defined_tags)):
            parsed_schedule = []
            schedule = instance.defined_tags['Schedule']
            for key, values in schedule.items():
                times = values.split(';')
                timedelta = []
                for i in times:
                    timedelta.append(
                        {'start': i.split('-')[0], 'stop': i.split('-')[1]})
                parsed_schedule_line = {
                    'schedule_day': key,
                    'schedule_times': timedelta
                }
                parsed_schedule.append(parsed_schedule_line)
            scheduled_instance_line = {
                'identifier': instance.identifier,
                'compartment': instance.compartment_id,
                'schedule': parsed_schedule}
            result.append(scheduled_instance_line)
    return result

# Check day/time and change the instance status


def start_stop_instances(instance_list, now):
    for instance in instance_list:
        # Sorting the shcedule in reverse alphabetical order so AnyDay is the lowest priority
        instance['schedule'].sort(
            key=lambda x: x['schedule_day'], reverse=True)
        for schedule in instance['schedule']:
            # 1st priority check: Day of the week
            if schedule['schedule_day'] in now.strftime('%A'):
                flag = False
                for t in schedule['schedule_times']:
                    start = convert_schedule_time(now, t['start'])
                    stop = convert_schedule_time(now, t['stop'])
                    if is_time_between(start.time(), stop.time(), now.time()):
                        flag = True
                if flag == True:
                    start_instance(instance['identifier'])
                else:
                    stop_instance(instance['identifier'])
                break
            # 2nd priority check: WeekDay or Weekend
            if schedule['schedule_day'] == 'Weekend':
                if now.strftime('%A') in ['Saturday', 'Sunday']:
                    flag = False
                    for t in schedule['schedule_times']:
                        start = convert_schedule_time(now, t['start'])
                        stop = convert_schedule_time(now, t['stop'])
                        if is_time_between(start.time(), stop.time(), now.time()):
                            flag = True
                    if flag == True:
                        start_instance(instance['identifier'])
                    else:
                        stop_instance(instance['identifier'])
                    break
            else:
                if schedule['schedule_day'] == 'WeekDay':
                    if now.strftime('%A') not in ['Saturday', 'Sunday']:
                        flag = False
                        for t in schedule['schedule_times']:
                            start = convert_schedule_time(now, t['start'])
                            stop = convert_schedule_time(now, t['stop'])
                            if is_time_between(start.time(), stop.time(), now.time()):
                                flag = True
                        if flag == True:
                            start_instance(instance['identifier'])
                        else:
                            stop_instance(instance['identifier'])
                        break
            # 3rd priority check: AnyDay
            if schedule['schedule_day'] == 'AnyDay':
                flag = False
                for t in schedule['schedule_times']:
                    start = convert_schedule_time(now, t['start'])
                    stop = convert_schedule_time(now, t['stop'])
                    if is_time_between(start.time(), stop.time(), now.time()):
                        flag = True
                if flag == True:
                    start_instance(instance['identifier'])
                else:
                    stop_instance(instance['identifier'])


# A helper function to determine if the current time is inbetween the two provided times


def is_time_between(begin_time, end_time, now):
    if begin_time < end_time:
        return now >= begin_time and now <= end_time
    else:  # crosses midnight
        return now >= begin_time or now <= end_time

# A helper function to convert the time string to datetime so it can be compared


def convert_schedule_time(now, timer):
    t = now.strftime("%Y-%m-%d") + " " + timer
    t = time.strptime(t, "%Y-%m-%d %H:%M")
    t = datetime.datetime(1970, 1, 1) + \
        datetime.timedelta(seconds=calendar.timegm(t))
    return t

# A helper function that processes the  argument for this script.


def prep_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('--compartment', default='',
                        help='The compartment where you want to stop/start all instances (optional)')
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    # Starts a timer for the execution time.
    print('Start/Stop instances v 0.3')
    start_time = datetime.datetime.now()
    print('Script execution start time: {0}'.format(
        start_time.replace(microsecond=0).isoformat()))

    # Set up config
    config = oci.config.from_file("~/.oci/config", "DEFAULT")
    # Create a service client
    identity = oci.identity.IdentityClient(config)
    base_compute = oci.core.compute_client.ComputeClient(config)

    region = config['region']
    tenancy = config['tenancy']

    base_compute.base_client.set_region(region)

    # Set the compartment, action, and time from arguments
    args = prep_arguments()
    compartment = args.compartment

    # This is the main function that finds instances in a compartment or region
    results = find_list_of_tagged_instances(compartment, region)
    results = parse_tags(results)
    start_stop_instances(results, start_time)

    # Completes the program and shows the duration of the run
    end_time = datetime.datetime.now()
    print('\nScript execution end time: {0}' .format(
        end_time.replace(microsecond=0).isoformat()))
    print('Duration: {0}' .format((end_time - start_time)))
