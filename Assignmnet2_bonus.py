import pandas as pd
from datetime import datetime
from datetime import timedelta
#from plot_day_schedule import *

# A main function for Alocating rooms and Anesthesiologists
def AllocateAnesthesiologistsAndRooms(SurgeriesSchedule):
    
    # Sort the Schedule by start time
    SurgeriesSchedule = SurgeriesSchedule.sort_values(by='start')

    # Initialize an empty dictionary to store allocations and relevant allocations
    Allocations = {}
    RelevantAllocationsByRooms = {};
    RelevantAllocationsByAnesthesiologists = {};    
    AnesthesiologistsShifts = {}
    OverWorked = [];   
    
    
    # The maximal AnesthesiologistsID assignd so far
    MaxAnesthesiologistsID = 0
    
    
    # Iterate over each surgery in the schedule
    for Index, Surgery in SurgeriesSchedule.iterrows():
               
        OverWorked = UpdateOverWorkedList(AnesthesiologistsShifts, OverWorked)
        
        # Delete non relevant (too early surgeries) from the relevant allocations lists
        RelevantAllocationsByRooms = DeleteNonRelevantAllocationsByRooms(RelevantAllocationsByRooms, Surgery);
        
        # Checks and assigns an available room for the surgery
        RoomID = AllocateRoom(RelevantAllocationsByRooms)
                
        if RoomID is None:            
            # If there is no available, we cannot assign anesthesiologist
            AnesthetistID = None
        else:
            
            RelevantAllocationsByAnesthesiologists = DeleteNonRelevantAllocationsByAnesthesiologists(RelevantAllocationsByAnesthesiologists, Surgery, RoomID);
            
            # Assigns anesthesiologist to the surgery
            AnesthetistID, MaxAnesthesiologistsID, AnesthesiologistsShifts, OverWorked = AllocateAnesthesiologist(RelevantAllocationsByAnesthesiologists, MaxAnesthesiologistsID, RoomID, AnesthesiologistsShifts, Surgery, OverWorked)

        # Add the allocation to the dictionary
        Allocations[Index] = {'start':  Surgery['start'], 'end':  Surgery['end'], 'anesthetist_id': AnesthetistID, 'room_id': RoomID}
        
        # Update the relevant allocation lists
        RelevantAllocationsByRooms[Index] = Allocations[Index]
        RelevantAllocationsByAnesthesiologists[Index] = Allocations[Index]

    # Create a new DataFrame with the allocations
    Schedule = pd.DataFrame.from_dict(Allocations, orient='index')
    Schedule.index.name = 'surgery_id'
        
    FullAnesthesiologistsShifts, Cost = CalculateCost(AnesthesiologistsShifts)
    
    Shifts = pd.DataFrame.from_dict(FullAnesthesiologistsShifts, orient='index')
    Shifts.index.name = 'AnesthesiologistsID'    
    Shifts.to_csv('Shifts.csv')
    
    print(f"Cost: {Cost}")
    
    # Plot the schedule
   # plot_day_schedule(Schedule)
    
    return Schedule

#
def UpdateOverWorkedList(AnesthesiologistsShifts, OverWorked):
    
    if len(AnesthesiologistsShifts) == 0:
        return OverWorked
    
    for AnesthesiologistID , AnesthesiologistShift in AnesthesiologistsShifts.items():
        StartTime = datetime.strptime(AnesthesiologistShift['start'], '%Y-%m-%d %H:%M:%S')
        EndTime = datetime.strptime(AnesthesiologistShift['end'], '%Y-%m-%d %H:%M:%S')        
        Duration = EndTime - StartTime
        DurationInSec = Duration.total_seconds()
        DurationInHours = DurationInSec //  3600
        if DurationInHours >= 12:
            OverWorked.append(AnesthesiologistID)
    
    OverWorked.sort()
    
    return OverWorked

# Delete non relevant (too early surgeries) from the relevant allocations lists
def DeleteNonRelevantAllocationsByRooms(RelevantAllocations, Surgery):
    if len(RelevantAllocations) == 0:
        return RelevantAllocations        
    else:
        # Get the starting time and end time for the current allocation
        StartTime = datetime.strptime(Surgery['start'], '%Y-%m-%d %H:%M:%S')
        
        # A list of key for non relvant allocations
        NonRelevntAllocationsKeys = [];
        
        # Iterating over the allocations
        for AllocationKey , Allocation in RelevantAllocations.items():
            
            # Get the starting time and end time for the relevant previous allocations
            AllocatedEndTime = datetime.strptime(Allocation['end'], '%Y-%m-%d %H:%M:%S')
            
            # If the start time of the current surgery is after the end of the previous surgey - we can delete it
            if StartTime >= AllocatedEndTime:
                NonRelevntAllocationsKeys.append(AllocationKey)
        
        # if there are non relevant surgeries - delete them
        if len(NonRelevntAllocationsKeys) > 0:
            for key in NonRelevntAllocationsKeys:
                 del RelevantAllocations[key]
    
    # return the updated allocation list
    return RelevantAllocations

# Delete non relevant (too early surgeries) from the relevant allocations lists
def DeleteNonRelevantAllocationsByAnesthesiologists(RelevantAllocations, Surgery, RoomID):
    if len(RelevantAllocations) == 0:
        return RelevantAllocations        
    else:
        # Get the starting time and end time for the current allocation
        StartTime = datetime.strptime(Surgery['start'], '%Y-%m-%d %H:%M:%S')
                
        # A list of key for non relvant allocations
        NonRelevntAllocationsKeys = [];
        
        # Iterating over the allocations
        for AllocationKey , Allocation in RelevantAllocations.items():
            
            # Get the starting time and end time for the relevant previous allocations
            AllocatedEndTime = datetime.strptime(Allocation['end'], '%Y-%m-%d %H:%M:%S')
            
            if RoomID == Allocation['room_id']:
                AdditionalTime = 0 
            else:
                AdditionalTime = 15
            
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
def AllocateAnesthesiologist(RelevantAllocations, MaxAnesthesiologistsID, RoomID, AnesthesiologistsShifts, Surgery, OverWorked):
    
    # if it is the first surgery - assign the first Anesthesiologist
    if len(RelevantAllocations) == 0:
        AnesthesiologistsShifts[0] =  {'start':  Surgery['start'], 'end':  Surgery['end']}
        return 0, MaxAnesthesiologistsID, AnesthesiologistsShifts, OverWorked;
    
    # Make a list of all occupied Anesthesiologists
    OccupiedAnesthesiologistsID = [];
    for _, Allocation in RelevantAllocations.items():
        OccupiedAnesthesiologistsID.append(int(Allocation['anesthetist_id']))
            
    OccupiedAnesthesiologistsID = [num for num in OccupiedAnesthesiologistsID if num not in OverWorked]
    
    # A list of all Anesthesiologists - so far
    AllAnesthesiologistsID = list(range(0, (MaxAnesthesiologistsID + 1)));    
    AllAnesthesiologistsID = [num for num in AllAnesthesiologistsID if num not in OverWorked]
    
    # A list of all avilable Anesthesiologists 
    SetDifference = set(AllAnesthesiologistsID).symmetric_difference(set(OccupiedAnesthesiologistsID))
    FreeAnesthesiologistsID = list(SetDifference)
    
    if FreeAnesthesiologistsID:
        # if there are avilable Anesthesiologists
        # Sort them by their ID and return the first avialable Anesthesiologist
        
        BestAnesthesiologistsIndex = -1
        BestAnesthesiologistsTime = 12
        for index, value in enumerate(FreeAnesthesiologistsID):
            AnesthesiologistShift = AnesthesiologistsShifts[value]  
            StartTime = datetime.strptime(AnesthesiologistShift['start'], '%Y-%m-%d %H:%M:%S')
            EndTime = datetime.strptime(Surgery['end'], '%Y-%m-%d %H:%M:%S')            
            Duration = EndTime - StartTime
            DurationInSec = Duration.total_seconds()
            DurationInHours = DurationInSec // 3600
            if DurationInHours < BestAnesthesiologistsTime:
                BestAnesthesiologistsTime = DurationInHours
                BestAnesthesiologistsIndex = value
        
        if BestAnesthesiologistsIndex < 0:
            # if there are no avilable Anesthesiologists
            # Call a new Anesthesiologists
            MaxAnesthesiologistsID = MaxAnesthesiologistsID + 1;
            AnesthesiologistsShifts[MaxAnesthesiologistsID] =  {'start':  Surgery['start'], 'end':  Surgery['end']}
            return MaxAnesthesiologistsID, MaxAnesthesiologistsID, AnesthesiologistsShifts, OverWorked
        else:
            SelectedAnesthesiologistsID = BestAnesthesiologistsIndex
            SelectedAnesthesiologistsShift = AnesthesiologistsShifts[SelectedAnesthesiologistsID]
            SelectedAnesthesiologistsShift['end'] = Surgery['end']
            AnesthesiologistsShifts[SelectedAnesthesiologistsID] = SelectedAnesthesiologistsShift
            return SelectedAnesthesiologistsID , MaxAnesthesiologistsID, AnesthesiologistsShifts, OverWorked
    else:
        # if there are no avilable Anesthesiologists
        # Call a new Anesthesiologists
        MaxAnesthesiologistsID = MaxAnesthesiologistsID + 1;
        AnesthesiologistsShifts[MaxAnesthesiologistsID] =  {'start':  Surgery['start'], 'end':  Surgery['end']}
        return MaxAnesthesiologistsID, MaxAnesthesiologistsID, AnesthesiologistsShifts, OverWorked

def CalculateCost(AnesthesiologistsShifts):
    Cost = 0.0
    FullAnesthesiologistsShifts = {}
    for  AnesthesiologistID, Shift in AnesthesiologistsShifts.items():
        StartTime = datetime.strptime(Shift['start'], '%Y-%m-%d %H:%M:%S')
        EndTime = datetime.strptime(Shift['end'], '%Y-%m-%d %H:%M:%S')
        Duration = EndTime - StartTime
        DurationInSec = Duration.total_seconds()
        DurationInHours = DurationInSec / 3600
        CostPerAnesthesiologist = max(5,DurationInHours) + (0.5*max(0,(DurationInHours - 9)))
        Cost = Cost + CostPerAnesthesiologist
        FullAnesthesiologistsShifts[AnesthesiologistID] = {'start':  Shift['start'], 'end':  Shift['end'], 'duration': DurationInHours, 'cost': CostPerAnesthesiologist}

    return FullAnesthesiologistsShifts, Cost

# ************ Running the assingmnet ****************

# Replace with the path to your CSV file
ScheduleFile = 'surgeries.csv'  

# Read the CSV file
SurgeriesSchedule = pd.read_csv(ScheduleFile) 

# Run the allocation progeam
Schedule = AllocateAnesthesiologistsAndRooms(SurgeriesSchedule) 

# Save the results
Schedule.to_csv('SurgeriesSchedule_Solution.csv')