# -*- coding: utf-8 -*-
"""
Created on Mon Dec 28 12:54:43 2020

@author: jpss8
"""
import matplotlib.pyplot as plt
import pandas as pd


def get_champion_name(champ_id):
    champ_used = next(champion for _,champion in championsData["data"].items() if champion["key"]==str(champ_id))
    champ_name = champ_used["name"]
    return champ_name


def sort_table_by_games(champ_name):
    return champ_name['games']


def sort_table_by_kda(champ_name):
    return champ_name['kda']


class Player:
    def __init__(self, name, account_id, lane, role):
        self.name = name
        self.account_id = account_id
        self.second_account_id = None
        self.lane = lane
        self.role = role
        self.kills = 0
        self.deaths = 0
        self.assists = 0
        self.kda = 0
        self.kda_values = []
        self.avg_last_10_kda = []
        self.damage = 0
        self.damage_percent = 0
        self.cs = 0
        self.gold = 0
        self.gold_percent = 0
        self.time_in_minutes = 0
        self.games = 0
        self.champions = {}
        self.vision = 0
        self.dragons = 0
        self.heralds = 0
        self.barons = 0
        self.fb = 0
        self.last_game_damage = 0
        self.last_game_gold = 0
        self.last_champ_used_name = 0

    def played_match(self, match_detail):
        return any(player for player in match_detail['participantIdentities'] if self.is_account_id(player["player"]["summonerId"]))

    def is_player_name(self, name_to_verify):
        return name_to_verify in [self.name]
    
    def is_account_id(self, id_to_verify):
        return id_to_verify in [self.account_id, self.second_account_id]

    def is_player_lane_and_role(self, lane, role):    #checks player lane and role
        return lane == self.lane and role == self.role
    
    def add_game_data(self, detail, game_duration, participant_timeline): #adds game data to player total stats and to champion played
        global championsData
        participant_stats = detail['stats']
        self.kills += participant_stats['kills']
        self.deaths += participant_stats['deaths']
        self.assists += participant_stats['assists']
        self.damage += participant_stats['totalDamageDealtToChampions']
        self.last_game_damage = participant_stats['totalDamageDealtToChampions']
        self.cs += participant_stats['neutralMinionsKilled'] + participant_stats['totalMinionsKilled']
        self.gold += participant_stats['goldEarned']
        self.last_game_gold = participant_stats['goldEarned']
        self.time_in_minutes += game_duration/60
        self.games += 1
        self.vision += participant_stats['visionScore']
        self.dragons += participant_timeline['dragons']
        self.heralds += participant_timeline['heralds']
        self.barons += participant_timeline['barons']
        self.fb += participant_timeline['fb']
        self.last_champ_used_name = get_champion_name(detail['championId'])
        champ_name = self.last_champ_used_name
        if champ_name in self.champions:
            champ_stats = self.champions[champ_name]
            champ_stats["games"] += 1
            champ_stats["kills"] += participant_stats['kills']
            champ_stats["assists"] += participant_stats['assists']
            champ_stats["deaths"] += participant_stats['deaths']
            champ_stats["damage"] += participant_stats['totalDamageDealtToChampions']
            champ_stats["last_game_damage"] = participant_stats['totalDamageDealtToChampions']
            champ_stats["cs"] += participant_stats['neutralMinionsKilled'] + participant_stats['totalMinionsKilled']
            champ_stats["gold"] += participant_stats['goldEarned']
            champ_stats["last_game_gold"] = participant_stats['goldEarned']
            champ_stats["time in minutes"] += game_duration/60
            champ_stats["vision"] += participant_stats['visionScore']
            champ_stats["cc"] += participant_stats['timeCCingOthers']
            champ_stats["dragons"] += participant_timeline['dragons']
            champ_stats["heralds"] += participant_timeline['heralds']
            champ_stats["barons"] += participant_timeline['barons']
            champ_stats["fb"] += participant_timeline['fb']
            
            if participant_stats["win"]:
                champ_stats['wins']+=1
        else:
            self.champions[champ_name] = {'games':1, 
                                          'kills':participant_stats['kills'], 
                                          'deaths':participant_stats['deaths'], 
                                          'assists':participant_stats['assists'], 'wins':0, 'kda':0, 
                                          'damage':participant_stats['totalDamageDealtToChampions'],
                                          'damage_percent':0,
                                          'cs':participant_stats['neutralMinionsKilled'] + participant_stats['totalMinionsKilled'],
                                          'gold':participant_stats['goldEarned'], 
                                          'gold_percent':0,
                                          'time in minutes':game_duration/60, 
                                          'vision':participant_stats['visionScore'],
                                          'cc':participant_stats['timeCCingOthers'], 'dragons':participant_timeline['dragons'],
                                          'heralds':participant_timeline['heralds'], 'barons':participant_timeline['barons'],
                                          'fb':participant_timeline['fb']
                                          }
            if participant_stats["win"]:
                self.champions[champ_name]['wins']+=1
  
        print(f"Finished processing player: {self}")
    
    def calculate_dmg_and_gold_percent(self, team_dmg, team_gold):
        if team_dmg != 0:
            self.damage_percent += self.last_game_damage*100/team_dmg
            self.gold_percent += self.last_game_gold*100/team_gold
            champ_name = self.last_champ_used_name
            if champ_name != 0:
                champ_stats = self.champions[champ_name]
                champ_stats['damage_percent'] += self.last_game_damage*100/team_dmg
                champ_stats['gold_percent'] += self.last_game_gold*100/team_gold

    def calculate_kda(self):  # calculates kda for player and for each champion
        avg_calc_games = 10
        if self.deaths == 0:
            self.kda = self.kills + self.assists
        else:
            self.kda = (self.kills + self.assists)/self.deaths
        for champ_name in self.champions:
            champ_stats = self.champions[champ_name]
            if champ_stats['deaths'] != 0:
                champ_stats['kda'] = (champ_stats['kills']+champ_stats['assists'])/champ_stats['deaths']
            else:
                champ_stats['kda'] = champ_stats['kills']+champ_stats['assists']
        for index in range(len(self.kda_values)):
            avg = 0
            for i in range(avg_calc_games):
                try:
                    avg += self.kda_values[index+i]
                except:
                    avg = 0
            self.avg_last_10_kda.append(avg/avg_calc_games)

    def save_kda_values(self, detail):
        stats = detail['stats']
        if stats['deaths'] == 0:
            kda = stats['kills'] + stats['assists']
        else:
            kda = (stats['kills'] + stats['assists'])/stats['deaths']
        self.kda_values.append(kda)
        
    def graph(self):
        plt.figure(self.name, figsize = (19.2,10.8)) #1920x1080
        
        plt.subplot(211)
        plt.plot(self.kda_values, 'bo', label='KDA in each game')
        plt.plot([0,self.games],[3,3], 'r', label='KDA=3')
        plt.plot(self.avg_last_10_kda, label='Last 10 games avg')
        plt.legend()
        plt.ylabel('kda')
        plt.grid(True)
        
        plt.subplot(212)
        total_games = 0
        for champ_name in self.champions:
            total_games += self.champions[champ_name]['games']
        for champ_name in self.champions:
            if self.champions[champ_name]['games'] > 5:    
                plt.bar(champ_name, self.champions[champ_name]['kda'], width = 3*self.champions[champ_name]['games']/total_games )
        plt.ylabel('kda')
        plt.suptitle(self.name)

    def __str__(self):
        return f"{self.name}: kills: {self.kills}, deaths:{self.deaths}, assists:{self.assists}, games:{self.games}" #todo fill out
    
    def get_all_stats(self):      #creates player row with general stats for team table and player table with all champions played
        team_table_row = {}  # row for each player in team table
        team_table_row['name'] = self.name
        team_table_row['kills per game'] = self.kills/self.games
        team_table_row['deaths per game'] = self.deaths/self.games
        team_table_row['assists per game'] = self.assists/self.games
        team_table_row['kda'] = self.kda
        team_table_row['dmg/min'] = self.damage/self.time_in_minutes
        team_table_row['avg dmg%'] =self.damage_percent/self.games
        team_table_row['cs/min'] = self.cs/self.time_in_minutes
        team_table_row['gold/min'] = self.gold/self.time_in_minutes
        team_table_row['avg gold%'] =self.gold_percent/self.games
        team_table_row['vision/min'] = self.vision/self.time_in_minutes
        team_table_row['dmg/gold'] = self.damage/self.gold
        team_table_row['games'] = self.games
        team_table_row['fbs/game'] = self.fb/self.games
             
        player_table=[] 
        for champ_name in self.champions:
            table2_row = {} #row for each champion in player table
            champ_stats = self.champions[champ_name]
            table2_row['champion'] = champ_name
            table2_row['games'] = champ_stats['games']
            table2_row['kills per game'] = champ_stats['kills']/champ_stats['games']
            table2_row['deaths per game'] = champ_stats['deaths']/champ_stats['games']
            table2_row['assists per game'] = champ_stats['assists']/champ_stats['games']
            table2_row['kda'] = champ_stats['kda']
            table2_row['win %'] = champ_stats['wins']*100/champ_stats['games']
            table2_row['dmg/min'] = champ_stats['damage']/champ_stats['time in minutes']
            table2_row['avg dmg%'] = champ_stats['damage_percent']/champ_stats['games']
            table2_row['cs/min'] = champ_stats['cs']/champ_stats['time in minutes']
            table2_row['gold/min'] = champ_stats['gold']/champ_stats['time in minutes']
            table2_row['avg gold%'] = champ_stats['gold_percent']/champ_stats['games']
            table2_row['avg game time'] = champ_stats['time in minutes']/champ_stats['games']
            table2_row['vision/min'] = champ_stats['vision']/champ_stats['time in minutes']
            table2_row['dmg/gold'] = champ_stats['damage']/champ_stats['gold']
            table2_row['dragons/game'] = champ_stats['dragons']/champ_stats['games']
            table2_row['heralds/game'] = champ_stats['heralds']/champ_stats['games']
            table2_row['barons/game'] = champ_stats['barons']/champ_stats['games']
            table2_row['fbs/game'] = champ_stats['fb']/champ_stats['games']
            player_table.append(table2_row)  
        player_table.sort(reverse=True, key=sort_table_by_kda)
        player_table.sort(reverse=True, key=sort_table_by_games)
        player_table = pd.DataFrame(player_table)
        
        return team_table_row, player_table

    def team_summary(self):  # todo
        print('games played = ', self.games)
        print('avg game time = ', self.time_in_minutes/self.games)