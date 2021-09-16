import numpy as np
import pandas as pd 
import random
import math

# General Info on script
"""Purpose is to automatically and randomly allocate accrediations to interested people taking into account their suitedness
    (by means of tier lists), gender and experience criteria. It does only provide a list of members that can be allocated
    to the available number of accreditations.
    
    Criteria:
    Suitedness:         based on ranking from KD-members. Deriving average values used to allocate entries to 
                        A_tier (avg 8-10), B_tier (avg. 4-8) and C_tier (1-4). It is ensured that number of entries
                        are chosen such that # A_tier > # B_tier > # C_tier
    Gender:             at least 50 % of accreditations should go to non-male individuals.
    Experience:         at least 60 % of accreditations should be given to individuals without past onground-COP/SB experience.
                        At least 1 individual with past experience has to be chosen.
                        
    It is strived to satisfy the criteria of gender & experience. However, it depends on the avialability and the characteristics
    of the submitted applications. Also, this is the first version of the nomiation tool. Hence, bugs or unwanted logic could occur.
    This code has been shared in advance with the KD-members to minimize errors and streamline the code. Thus, the best possible
    code is used for the selection process.
    
    Input parameters:
    Name:               Not considered during process.
    Wochenpraeferenz:   availability in COP weeks (1- 1st week, 2- 2nd week, 3 - flexible)
    AH:                 Alte Haes:innen (with onground experience)
    Gender:             m - male, nm - non-male
    Ranking:            Average ranking derived in a previous processing step
    """

# Functions
def probabilistic_round(x):
    return int(math.floor(x + random.random()))

def ExtendedLists(A_tier,B_tier,C_tier,number_accred):
    """Create different entry pools consiting of different tier lists. 
    A_tier:         all entries with x >= 8
    B_tier:         all entries with 4 < x < 8
    C_tier:         all entries with x <= 4
    """
    A_tier = A_tier
    AB_tier = A_tier.append(B_tier)
    ABC_tier = AB_tier.append(C_tier)

    return [A_tier,AB_tier,ABC_tier]
      
def optimizeTierChoice(exist_shortlist,input_list,number_accred):
    """Function to select as many people from A_tier as possible. Experience used as dominant criterion.
        In case A_tier is not sufficient to satisfy the criteria, a maximum number of entries from A_tier 
        is used while random entries are dropped to keep the short list in accordance with requrirements
        from global criteria. Function is used in the furter process of the function RandomDrawer().
        
        exist_shortlist:    correponds in 1st Round to the first sample iteration from A_tier, and in the 2nd round to the
                            already optimized short list from the 1st round.
        input_list:         either A_tier (1st round) or AB_tier (2nd round)
        number_accred:      number of accreditations"""
    # 0. Remove already existing entries in exist_shortlist from input_list
    input_list = pd.merge(input_list,exist_shortlist, indicator=True, how='outer').query('_merge=="left_only"').drop('_merge', axis=1)

    # 1. Sample entries from input list 
    short_list = exist_shortlist.append(input_list.sample(min(len(input_list),number_accred - len(exist_shortlist)), replace=False))

    # 2. Check if, and if yes, how many initial short list contains too many entries with experience 
    removals = max(0,len(short_list[short_list["AH"] == "ja"]) - max(1,math.floor(2/5 * number_accred)))

    # 3. Drop random entries with experience to ensure that not too many "ja" are present (i.o.t. meet experience criterion)
    short_list_temp = short_list.drop(short_list.query('AH == "ja"').sample(removals, replace=False).index)

    # 4. Remove already selected entries from input list
    short_list_add = pd.merge(input_list,short_list_temp, indicator=True, how='outer').query('_merge=="left_only"').drop('_merge', axis=1)

    # 4. Draw additional entries with "nein" from highest list based on number of removed entries due to criterion
    if removals == 0:
        short_list = short_list_temp
        print("AH: No entries removed.")
    elif removals > len(short_list_add[short_list_add['AH'] == "nein"]):
        short_list = short_list_temp.append(short_list_add[short_list_add['AH'] == "nein"])
        print("AH:", len(short_list), "entries are used, while it could be", number_accred, ".")
    else:
        short_list_add = short_list_add[short_list_add['AH'] == "nein"].sample(removals, replace=False)
        short_list = short_list_temp.append(short_list_add)
        print("AH:", len(short_list), len(short_list), "entries are randomly selected.")

    # 5. Repeat steps 1.-4. for the gender criterion 
    removals = max(0,len(short_list[short_list["Gender"] == "m"]) - math.floor(0.5 * number_accred))
    short_list_temp = short_list.drop(short_list.query('Gender == "m"').sample(removals, replace=False).index)
    short_list_add = pd.merge(input_list,short_list_temp, indicator=True, how='outer').query('_merge=="left_only"').drop('_merge', axis=1)
    if removals == 0:
        short_list = short_list_temp
        print("Gender: No entries removed.")
    elif removals > len(short_list_add[short_list_add['Gender'] == "nm"]):
        short_list = short_list_temp.append(short_list_add[short_list_add['Gender'] == "nm"])
        print("Gender:", len(short_list), "entries are used, while it could be", number_accred, ".")
    else:
        short_list_add = short_list_add[short_list_add['Gender'] == "nm"].sample(removals, replace=False)
        short_list = short_list_temp.append(short_list_add)
        print("Gender:", len(short_list), "entries are randomly selected.")

    return short_list

def randomDrawer(A_Tier,AB_Tier, ABC_Tier,number_accred,n):
    """This function draws random samples from varying lists starting with A_tier to satisfy the criteria and ensuring
        highest number of people from A_tier in the final short list.
        A_Tier:         Entries with average rank >= 8
        AB_Tier:        Entries with average rank > 4
        ABC_Tier:       Entries with average rank > 1
        n:              number of iterations used to find the optimum entri combination"""
        
    # 1. Iterate to find criteria satisfying entry combination
    for i in range(0,n):
        # Resample short_list in case criterion (below) is not met
        short_list = A_Tier.sample(n=min(number_accred,len(A_Tier)), replace=False)
        # 1.1 Criterion can be reached
        if (len(short_list) == number_accred) and len(short_list[short_list["Gender"] == "nm"]) >= math.ceil(number_accred/2) and len(short_list[short_list["AH"] == "ja"]) <= max(1,math.floor(number_accred * 2/5)):
            print("Iteration step ", i, ": First Round - A_Tier satisfies requirements")
            short_list_final = short_list
            break
            
        # 1.2 Criterion cannot be reached
        if i == n-1:
            print('First Round: It is not possible to satisfy all criteria by extending the list')

            # Extend entry pool and find combination to satisfy the criteria
            # 1.2.1 Run function to choose as many entries from the highest tier as possible 
            short_list = optimizeTierChoice(short_list,A_Tier, number_accred)  
                
            # 1.2.2 Identify number of available spots that have to be filled from the lower tiers
            additional_list = max(0,number_accred - len(short_list))

            # 1.2.3 Remove already selected entries from extended list
            input_list_extended = pd.merge(AB_Tier,short_list, indicator=True, how='outer').query('_merge=="left_only"').drop('_merge', axis=1)

            # 1.2.4 Use loop again to Sample entries from reduced extended list based on number of free spots to find criterion-satisfying choice from reduced extended list
            for j in range(0,n):
                short_list_extended = input_list_extended.sample(n=min(len(input_list_extended),additional_list), replace=False)
                temp = short_list.append(short_list_extended)

                # 1.2.4.1 Criterion can be reached
                if (len(temp) == number_accred) and len(temp[temp["Gender"] == "nm"]) >= math.ceil(number_accred/2) and len(temp[temp["AH"] == "ja"]) <= max(1,math.floor(number_accred * 2/5)): 
                    print("2nd Round: List was extended and does satisfy all global criteria.")
                    short_list_final = temp 
                    break
                # 1.2.4.2 Criterion cannot be reached
                if j == n-1:
                    print('2nd Round: It is not possible to satisfy all criteria by extending the list')                
                    # 1.2.4.2.1 Repeat above steps by extending the entry pool
                    short_list = optimizeTierChoice(temp,AB_Tier, number_accred)

                    # 1.2.4.2.2 identify number of available spots that have to be filled from the lower tiers
                    additional_list = number_accred - len(short_list)

                    # 1.2.4.2.3 Remove already selected entries from extended list
                    input_list_extended = pd.merge(ABC_Tier,short_list, indicator=True, how='outer').query('_merge=="left_only"').drop('_merge', axis=1)

                    # 1.2.4.2.5 Use loop again to find criterion-satisfying choice from reduced extended list
                    for j in range(0,n):
                        short_list_extended = input_list_extended.sample(n=additional_list, replace=False)
                        temp = short_list.append(short_list_extended)

                        # 1.2.4.2.5.1 Criterion can be reached
                        if (len(temp) == number_accred) and len(temp[temp["Gender"] == "nm"]) >= math.ceil(number_accred/2) and len(temp[temp["AH"] == "ja"]) <= max(1,math.floor(number_accred * 2/5)): 
                            print("3rd Round: List was extended and does satisfy all global criteria.")
                            short_list_final = temp 
                            break
                        # 1.2.4.2.5.2 Criterion cannot be reached
                        else:
                            short_list_final = temp
                            print('3rd Round: It is not possible to satisfy all criteria')
                            break
    return short_list_final

# Define Inputs
number_accred = [8,8]   # [number of accreditations week 1, number of accreditations week 2]
n = 1000            # number of iterations


# Import ranking lists
rank_liste = pd.read_excel('Rankings.xlsx')

# Allocate "flexible people" randomly to either week (only possible if majority of people indicate that they are flexible)
# Round up or down randomly in case an odd number of entries are present
if isinstance(len(rank_liste)/ 2,int) == True:
    week1_selection = len(rank_liste)/ 2
else:
    week1_selection = probabilistic_round(len(rank_liste)/ 2)

flexible_week1 = week1_selection - len(rank_liste[rank_liste["Wochenpraeferenz"] == 1])

week1_replacement_index = rank_liste[rank_liste["Wochenpraeferenz"] == 3].sample(n = flexible_week1, replace=False).index.tolist()

for k in range(len(week1_replacement_index)):
    print(k)
    rank_liste.iat[week1_replacement_index[k],1] = 1
rank_liste.loc[(rank_liste["Wochenpraeferenz"] == 3),"Wochenpraeferenz"] = 2

# rank_liste = rank_liste[]

# Create tier_lists
rank_liste["Ranking"] = rank_liste["Ranking"].astype(float)
A_tier = rank_liste[rank_liste["Ranking"] >= 8]
B_tier = rank_liste[(rank_liste["Ranking"] > 4) & (rank_liste["Ranking"] < 8)]
C_tier = rank_liste[rank_liste["Ranking"] <= 4]




# Run Code for both weeks
for week in [1,2]:
    if week == 1:
        print("Week 1", "\n")
        # Create sub-lists of all tier_lists
        w1_A_tier = A_tier[A_tier["Wochenpraeferenz"] == week]
        w1_B_tier = B_tier[B_tier["Wochenpraeferenz"] == week]
        w1_C_tier = C_tier[C_tier["Wochenpraeferenz"] == week]
        print(w1_C_tier)
        # Create different entry pools
        [w1_A_tier,w1_AB_tier,w1_ABC_tier] = ExtendedLists(w1_A_tier,w1_B_tier,w1_C_tier,number_accred[0])

        # Find optimum short lists
        week1 = randomDrawer(w1_A_tier,w1_AB_tier,w1_ABC_tier,number_accred[0],n)
        week1.drop('Ranking',axis=1, inplace=True)
        week1.to_csv("week1.txt")

    else:
        print("Week 2", "\n")
        # Remove entries that were used in week1 already
        A_tier = pd.merge(A_tier,week1, indicator=True, how='outer').query('_merge=="left_only"').drop('_merge', axis=1)
        B_tier = pd.merge(B_tier,week1, indicator=True, how='outer').query('_merge=="left_only"').drop('_merge', axis=1)
        C_tier = pd.merge(C_tier,week1, indicator=True, how='outer').query('_merge=="left_only"').drop('_merge', axis=1)
        
        # Create sub-lists of all tier_lists
        w2_A_tier = A_tier[A_tier["Wochenpraeferenz"] == week]
        w2_B_tier = B_tier[B_tier["Wochenpraeferenz"] == week]
        w2_C_tier = C_tier[C_tier["Wochenpraeferenz"] == week]
        print(w2_C_tier)
        
        # Create different entry pools
        [w2_A_tier,w2_AB_tier,w2_ABC_tier] = ExtendedLists(w2_A_tier,w2_B_tier,w2_C_tier,number_accred[1])

        # Find optimum short lists
        week2 = randomDrawer(w2_A_tier,w2_AB_tier,w2_ABC_tier,number_accred[1],n)
        week2.drop('Ranking',axis=1, inplace=True)
        week2.to_csv("week2.txt")
delegate_choices = week1.append(week2)
rank_liste.drop('Ranking',axis=1, inplace=True)
waitinglist = pd.merge(rank_liste,delegate_choices, indicator=True, how='outer').query('_merge=="left_only"').drop('_merge', axis=1)
# waitinglist.drop('Ranking',axis=1, inplace=True)
print(waitinglist)









