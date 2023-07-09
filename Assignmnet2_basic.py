import pandas as pd
from datetime import datetime
from datetime import timedelta
from plot_day_schedule import *

# A main function for Alocating rooms and Anesthesiologists
def AllocateAnesthesiologistsAndRooms(SurgeriesSchedule):
    
    # Sort the Schedule by start time
    SurgeriesSchedule = SurgeriesSchedule.sort_values(by='start')

    # Initialize an empty dictionary to store allocations and relevant allocations
    Allocations = {}
    RelevantAllocationsByRooms = {};
    RelevantAllocationsByAnesthesiologists = {};    
    
    # The maximal AnesthesiologistsID assignd so far
    MaxAnesthesiologistsID = 0
    
    # Iterate over each surgery in the schedule
    for Index, Surgery in SurgeriesSchedule.iterrows():
        
        # Delete non relevant (too early surgeries) from the relevant allocations lists
        RelevantAllocationsByRooms = DeleteNonRelevantAllocations(RelevantAllocationsByRooms, Surgery, False);
        RelevantAllocationsByAnesthesiologists = DeleteNonRelevantAllocations(RelevantAllocationsByAnesthesiologists, Surgery, True);
        
        # Checks and assigns an available room for the surgery
        RoomID = AllocateRoom(RelevantAllocationsByRooms)
                
        if RoomID is None:            
            # If there is no available, we cannot assign anesthesiologist
            AnesthetistID = None
        else:
            # Assigns anesthesiologist to the surgery
            AnesthetistID, MaxAnesthesiologistsID = AllocateAnesthesiologist(RelevantAllocationsByAnesthesiologists, MaxAnesthesiologistsID, RoomID)

        # Add the allocation to the dictionary
        Allocations[Index] = {'start':  Surgery['start'], 'end':  Surgery['end'], 'anesthetist_id': AnesthetistID, 'room_id': RoomID}
        
        print(Allocations[Index])
        
        # Update the relevant allocation lists
        RelevantAllocationsByRooms[Index] = Allocations[Index]
        RelevantAllocationsByAnesthesiologists[Index] = Allocations[Index]

    # Create a new DataFrame with the allocations
    Schedule = pd.DataFrame.from_dict(Allocations, orient='index')
    Schedule.index.name = 'surgery_id'
    
    # Plot the schedule
    plot_day_schedule(Schedule)
    
    return Schedule

# Delete non relevant (too early surgeries) from the relevant allocations lists
def DeleteNonRelevantAllocations(RelevantAllocations, Surgery, IsAnesthesiologists):
    if len(RelevantAllocations) == 0:
        return RelevantAllocations        
    else:
        # Get the starting time and end time for the current allocation
        StartTime = datetime.strptime(Surgery['start'], '%Y-%m-%d %H:%M:%S')
        
        # If this is an Anesthesiologists, we need to add 15 mintus to switch rooms
        if IsAnesthesiologists:
            AdditionalTime = 15
        else:
            AdditionalTime = 0
        
        # A list of key for non relvant allocations
        NonRelevntAllocationsKeys = [];
        
        # Iterating over the allocations
        for AllocationKey , Allocation in RelevantAllocations.items():
            
            # Get the starting time and end time for the relevant previous allocations
            AllocatedEndTime = datetime.strptime(Allocation['end'], '%Y-%m-%d %H:%M:%S')
            
            # If the start time of the current surgery is after the end of the previous surgey - we can delete it
            if StartTime >= (AllocatedEndTime + timedelta(minutes=AdditionalTime)):
                NonRelevntAllocationsKeys.append(AllocationKey)
        
        # if there are non relevant surgeries - delete them
        if len(NonRelevntAllocationsKeys) > 0:
            for key in NonRelevntAllocationsKeys:
                 del RelevantAllocations[key]
    
    # return the updated allocation list
    return RelevantAllocations
       

# Checks and assigns an available room for the surgery
def AllocateRoom(RelevantAllocations):
    
    # if it is the first surgery - assign the first room
    if len(RelevantAllocations) == 0:
        return 0;
    
    # Make a list of all occupied rooms
    OccupiedRoomsID = [];
    for _, Allocation in RelevantAllocations.items():
        OccupiedRoomsID.append(int(Allocation['room_id']))        
    
    # a list of all rooms
    AllRoomsID = list(range(0, 20));    
    
    # A list of all avialable rooms
    SetDifference = set(AllRoomsID).symmetric_difference(set(OccupiedRoomsID))
    FreeRoomsID = list(SetDifference)
        
    if FreeRoomsID:
        # Sort the avialable rooms by ID and return the first avialable room
        FreeRoomsID.sort()
        return FreeRoomsID[0]
    else:
        # There is no avialable room
        return None


# Assigns anesthesiologist to the surgery
def AllocateAnesthesiologist(RelevantAllocations, MaxAnesthesiologistsID, RoomID):
    
    # if it is the first surgery - assign the first Anesthesiologist
    if len(RelevantAllocations) == 0:
        return 0, MaxAnesthesiologistsID;
    
    # Make a list of all occupied Anesthesiologists
    OccupiedAnesthesiologistsID = [];
    for _, Allocation in RelevantAllocations.items():
        if RoomID != int(Allocation['anesthetist_id']):
            OccupiedAnesthesiologistsID.append(int(Allocation['anesthetist_id']))
    
    # A list of all Anesthesiologists - so far
    AllAnesthesiologistsID = list(range(0, (MaxAnesthesiologistsID + 1)));    
    
    # A list of all avilable Anesthesiologists 
    SetDifference = set(AllAnesthesiologistsID).symmetric_difference(set(OccupiedAnesthesiologistsID))
    FreeAnesthesiologistsID = list(SetDifference)
    
    if FreeAnesthesiologistsID:
        # if there are avilable Anesthesiologists
        # Sort them by their ID and return the first avialable Anesthesiologist
        FreeAnesthesiologistsID.sort()
        return FreeAnesthesiologistsID[0] , MaxAnesthesiologistsID
    else:
        # if there are no avilable Anesthesiologists
        # Call a new Anesthesiologists
        MaxAnesthesiologistsID = MaxAnesthesiologistsID + 1;
        return MaxAnesthesiologistsID, MaxAnesthesiologistsID


# ************ Running the assingmnet ****************

# Replace with the path to your CSV file
ScheduleFile = 'surgeries.csv'  

# Read the CSV file
SurgeriesSchedule = pd.read_csv(ScheduleFile) 

# Run the allocation progeam
Schedule = AllocateAnesthesiologistsAndRooms(SurgeriesSchedule) 

# Save the results
Schedule.to_csv('SurgeriesSchedule_Solution.csv')