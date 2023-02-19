# -*- coding: utf-8 -*-
"""
Created on Tue Jun  2 14:07:35 2020

@author: jpss8 && Jowker
"""

from player import Player
import json
from riotwatcher import LolWatcher, ApiError
import pandas as pd


with open('champion.json', 'r', encoding="utf8") as f:
    championsData=f.read()
    championsData=json.loads(championsData)

# global variables
api_key = '{your api key here}'
watcher = LolWatcher(api_key)
my_region = '{your region here, ex: la2}'


def get_players():     #now also creates an enemy team and assigns lanes and roles
    ally_player_names = ["{id1}", "{id1}", "{id1}", "{id1}", "{id1}"]  # make input
    lanes = ["TOP", "JUNGLE", "MIDDLE", "BOTTOM", "BOTTOM"]
    roles = ["SOLO", "NONE", "SOLO", "DUO_CARRY", "DUO_SUPPORT"]
    enemy_player_names = ["enemy top", "enemy jg","enemy mid","enemy adc","enemy support"]
    ally_players = {}
    enemy_players = {}         
    for index, (ally, enemy) in enumerate(zip(ally_player_names,enemy_player_names)):
        account_id = watcher.summoner.by_name(my_region, ally)["id"]
        ally_players[ally] = Player(ally, account_id, lanes[index], roles[index])
        enemy_players[enemy] = Player(enemy, None, lanes[index], roles[index])  
    return ally_players, enemy_players


def are_all_players_in_match(players, match_detail):
    return len([player for _, player in players.items() if player.played_match(match_detail)]) == len(players)


def analyze_timeline(match_timeline):
    participants_timeline_stats = []
    fb_flag = 1
    for participant_id in range(10):  # 10 people per game
        participants_timeline_stats.append({'dragons':0, 'heralds':0, 'barons':0, 'fb':0})
    for timeframe in match_timeline['frames']:
        for event_index in timeframe['events']:
            if event_index['type'] == "ELITE_MONSTER_KILL":
                participant = participants_timeline_stats[event_index['killerId']-1]        
                if event_index['monsterType'] == "DRAGON":
                    participant['dragons'] += 1    
                elif event_index['monsterType'] == "RIFTHERALD":
                    participant['heralds'] += 1
                elif event_index['monsterType'] == "BARON_NASHOR":
                    participant['barons'] += 1
                
            if event_index['type'] == "CHAMPION_KILL" and fb_flag == 1:
                participant = participants_timeline_stats[event_index['killerId']-1]
                participant['fb'] += 1
                for assisting_participant in event_index['assistingParticipantIds']:
                    participants_timeline_stats[assisting_participant-1]['fb'] += 1
                fb_flag = 0
    return participants_timeline_stats


def analyze_match(match_to_analyze, ally_players, enemy_players):
    enemy_players_index = 0
    ally_team_dmg = 0
    ally_team_gold = 0
    enemy_team_dmg = 0
    enemy_team_gold = 0
    red = {'games':0, 'wins':0, 'fblood':0, 'soul':{'secured':0, 'total':0}, 'dragons':{'secured':0, 'total':0}, 'heralds':{'secured':0, 'total':0}, 'barons':{'secured':0, 'total':0}}
    blue = {'games':0, 'wins':0, 'fblood':0, 'soul':{'secured':0, 'total':0}, 'dragons':{'secured':0, 'total':0}, 'heralds':{'secured':0, 'total':0}, 'barons':{'secured':0, 'total':0}}
    side_stats = {'blue':blue , 'red':red}
    enemy_player_names = ["enemy top", "enemy jg","enemy mid","enemy adc","enemy support"]
    match_detail, match_timeline = get_from_api(match_to_analyze)
    if are_all_players_in_match(ally_players, match_detail):
        participants_timelines = analyze_timeline(match_timeline)
        for player_name in ally_players:
            for participant in match_detail['participantIdentities']:
                participant_id = participant['participantId']-1
                participant_timeline = participants_timelines[participant_id]
                team_id = match_detail['participants'][participant_id]['teamId']
                lane_and_role = match_detail['participants'][participant_id]['timeline']
                participant_detail = match_detail['participants'][participant_id]
                game_duration = match_detail['gameDuration']
                if ally_players[player_name].is_account_id(participant['player']['summonerId']): # checks for ally_players
                    ally_players[player_name].add_game_data(participant_detail, game_duration, participant_timeline)
                    ally_team_dmg += participant_detail['stats']['totalDamageDealtToChampions']
                    ally_team_gold += participant_detail['stats']['goldEarned']
                    if team_id == 100:
                        ally_team_detail = match_detail['teams'][0]
                        enemy_team_detail = match_detail['teams'][1]
                        side = 'blue'
                    else:
                        ally_team_detail = match_detail['teams'][1]
                        enemy_team_detail = match_detail['teams'][0]
                        side = 'red'
                    if ally_team_detail['win'] == 'Win':
                        side_stats[side]['wins'] = 1 
                    side_stats[side]['games'] = 1
                    side_stats[side]['dragons']['secured'] = ally_team_detail['dragonKills']
                    side_stats[side]['dragons']['total'] = ally_team_detail['dragonKills'] + enemy_team_detail['dragonKills']
                    side_stats[side]['heralds']['secured'] = ally_team_detail['riftHeraldKills']
                    side_stats[side]['heralds']['total'] = ally_team_detail['riftHeraldKills'] + enemy_team_detail['riftHeraldKills']
                    side_stats[side]['barons']['secured'] = ally_team_detail['baronKills']
                    side_stats[side]['barons']['total'] = ally_team_detail['baronKills'] + enemy_team_detail['baronKills']
                    side_stats[side]['fblood'] = int(ally_team_detail['firstBlood'])
                    if ally_team_detail['dragonKills'] >= 4: # not 100% correct, 4 dragons should make a soul in most cases
                        side_stats[side]['soul']['secured'] = 1
                        side_stats[side]['soul']['total'] = 1
                    elif enemy_team_detail['dragonKills'] >= 4:
                        side_stats[side]['soul']['total'] = 1
                        
                    ally_players[player_name].save_kda_values(participant_detail)
                    
                elif ally_players[player_name].is_player_lane_and_role(lane_and_role['lane'], lane_and_role['role']): #when it's not an ally checks for their lane and role
                    enemy_players[enemy_player_names[enemy_players_index]].add_game_data(participant_detail, game_duration, participant_timeline)
                    enemy_team_dmg += participant_detail['stats']['totalDamageDealtToChampions']
                    enemy_team_gold += participant_detail['stats']['goldEarned']
            enemy_players_index += 1                                        
        for name in ally_players:
            ally_players[name].calculate_dmg_and_gold_percent(ally_team_dmg, ally_team_gold)
        if enemy_team_dmg != 0: #condition for weird cases in which the game fails in lane and role identification of ALL 5 enemies
            for name in enemy_players:
                enemy_players[name].calculate_dmg_and_gold_percent(enemy_team_dmg, enemy_team_gold)
        return side_stats
    return side_stats


def get_match_ids(ammount_to_analyze):  # puts all match ids in one list
    account = watcher.summoner.by_name(my_region, '{an ign}')
    matches = []
    counter = 0
    begin_index = 0
    if ammount_to_analyze < 100:
        end_index = ammount_to_analyze
    else:
        end_index=100
    while ammount_to_analyze > 100:
        counter += 1
        ammount_to_analyze -= 100
    while counter > -1:
        matches.extend(watcher.match.matchlist_by_account(my_region, account['accountId'], queue=440, begin_time=1605457737000 , begin_index=begin_index, end_index=end_index)['matches'])
        # queue_id 440 = flex
        # 1st begin time is may 16 2020 = 1589671546000
        # 1st end time is oct 27 2020 = 1603773304000
        # 2nd begin time is nov 15 2020 = 1605457737000
        counter -= 1
        if counter > 0:
            end_index += 100
            begin_index += 100
        else:
            begin_index += 100
            end_index += ammount_to_analyze
    return matches


def get_from_api(match_to_analyze):
    try:
        match_detail = watcher.match.by_id(my_region, match_to_analyze['gameId'])
        match_timeline = watcher.match.timeline_by_match(my_region, match_to_analyze['gameId'])
        return match_detail, match_timeline
    except:
        return get_from_api(match_to_analyze)


def run():
    ammount_to_analyze = 30 #todo input
    matches = get_match_ids(ammount_to_analyze)
    
    ally_players, enemy_players = get_players()
    
    red = {'games':0, 'wins':0, 'fblood':0, 'soul':{'secured':0, 'total':0}, 'dragons':{'secured':0, 'total':0}, 'heralds':{'secured':0, 'total':0}, 'barons':{'secured':0, 'total':0}}
    blue = {'games':0, 'wins':0, 'fblood':0, 'soul':{'secured':0, 'total':0}, 'dragons':{'secured':0, 'total':0}, 'heralds':{'secured':0, 'total':0}, 'barons':{'secured':0, 'total':0}}
    total_side_stats = {'blue':blue , 'red':red}
    for match_to_analyze in matches:
        side_stats = analyze_match(match_to_analyze, ally_players, enemy_players)
        for side in total_side_stats:
            for key in total_side_stats[side]:
                try:    
                    total_side_stats[side][key] += side_stats[side][key]
                except:
                    total_side_stats[side][key]['secured'] += side_stats[side][key]['secured']
                    total_side_stats[side][key]['total'] += side_stats[side][key]['total']
                
    ally_player_stats=[]
    ally_team_stats=[]
    enemy_player_stats=[]
    enemy_team_stats=[]  
    flag = 0
    for name, player in ally_players.items():
        player.calculate_kda()
        team_stats_aux, player_stats_aux = player.get_all_stats()
        ally_team_stats.append(team_stats_aux)
        ally_player_stats.append(player_stats_aux)
        player.graph()
        if flag == 0:
            player.team_summary()
            flag = 1
    ally_team_stats = pd.DataFrame(ally_team_stats)
    
    for name, player in enemy_players.items():
        player.calculate_kda()
        team_stats_aux, player_stats_aux = player.get_all_stats()
        enemy_team_stats.append(team_stats_aux)
        enemy_player_stats.append(player_stats_aux)
    enemy_team_stats = pd.DataFrame(enemy_team_stats)
    
    
    
    total_games = total_side_stats['blue']['games'] + total_side_stats['red']['games']
    wins = total_side_stats['blue']['wins'] + total_side_stats['red']['wins']
    print('WR = ', wins*100/total_games)
    for side in total_side_stats:
        print('total ', side, ' stats')
        if total_side_stats[side]['games'] != 0:
            print(side, ' WR = ', total_side_stats[side]['wins']*100/total_side_stats[side]['games'], "games: ",total_side_stats[side]['games'])
        if total_side_stats[side]['games'] != 0:
            print(side, ' FB% = ', total_side_stats[side]['fblood']*100/total_side_stats[side]['games'])
        if total_side_stats[side]['dragons']['total'] != 0:
            print(side, ' Dragon% = ', total_side_stats[side]['dragons']['secured']*100/total_side_stats[side]['dragons']['total'])
        if total_side_stats[side]['soul']['total'] != 0:
            print(side, ' Soul% = ', total_side_stats[side]['soul']['secured']*100/total_side_stats[side]['soul']['total'])
        if total_side_stats[side]['heralds']['total'] != 0:
            print(side, ' RH% = ', total_side_stats[side]['heralds']['secured']*100/total_side_stats[side]['heralds']['total'])
        if total_side_stats[side]['barons']['total'] != 0:
            print(side, ' BN% = ', total_side_stats[side]['barons']['secured']*100/total_side_stats[side]['barons']['total'])
    
    return ally_team_stats, ally_player_stats, enemy_team_stats, enemy_player_stats

if __name__ == "__main__":
    ally_team_stats, ally_player_stats, enemy_team_stats, enemy_player_stats = run()