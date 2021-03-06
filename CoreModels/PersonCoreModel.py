#!/usr/bin/env python
# coding=utf-8
# PersonCoreModel.py
import logging
import datetime
import pprint
from BaseCoreModel import BaseCoreModel
from _exceptions.http_error import DBQueryError
from bson import ObjectId
class PersonCoreModel(BaseCoreModel):
    def __init__(self, *argc, **argkw):
        super(PersonCoreModel, self).__init__(*argc, **argkw)
        self.CAMERA = 0
        self.PERSON = 1
        self.POLICE = 2
        self.PERSON_SEARCH = 3

    def insert_person_info(self,pic_key, info_data):
        info_data['picture_key_list'] = pic_key
        info_data['formal'] = info_data['formal']
        info_data['track_list'] = []
        info_data['last_update_time'] = info_data['lost_time']
        info_data['last_update_spot'] = info_data['lost_spot']
        return self.mongodb.person.info.insert_one(info_data).inserted_id

    def delete_person(self,person_id):
        if type(person_id) == str:
            person_id = ObjectId(person_id)
        return self.mongodb.person.info.delete_one({'_id':person_id})

    def update_person_picture(self,person_id,picture_key_list):
        data = {
            'picture_key_list':picture_key_list
        }
        if type(person_id) == str:
            person_id = ObjectId(person_id)
        self.mongodb.person.info.update({'_id':person_id},{'$set':data},multi=False)

    def update_persons_relation_id(self,person_list,relation_id):
        """Update missing person's relation uid filter by person_list:

        Args:
            person_list: missing person id list
            relation_id
        """
        id_list = [{'_id':x} for x in person_list]
        data = {'relation_id':relation_id}
        # db.getCollection('person.info').update({$or:[{relation_id:51},{relation_id:50}]},{age:21})
        # db.getCollection('person.info').update({$or:[{relation_id:51},{relation_id:49}]},{$set:{age:21}})
        # db.getCollection('person.info').update({$or:[{relation_id:51},{relation_id:49}]},{$set:{age:21}},{multi:true})
        if id_list != []:
            self.mongodb.person.info.update({'$or':id_list},{'$set':data},multi=True)
    
    def find_persons_by_tele(self,telephone):
        """query from person.info by telephone.

        Args && example:
            "telephone":"15195861110",
            
        Returns:
            person_list: missing person list identify by '_id'
        """
        cursor = self.mongodb.person.info.find({'relation_telephone':telephone})
        person_list = []
        if cursor != None:
            for item in cursor:
                person_list.append(item['_id'])
        return person_list

    def get_person_info_by_date(self, filter_info,offset,is_formal):
        """filter person info by last update time.

        Args:
            filter_info
            offset
            is_formal: 0 stand for not formal; 1 stand for formal; 2 stand for all include formal and not formal.

        Returns:
        """
        skip = offset['page'] * offset['size']
        size = offset['size']
        find_info = {
            'last_update_spot':{
                '$geoWithin':{
                    '$center':[filter_info['spot'],filter_info['max_distance']]
                }
            }
        }
        if is_formal != 2:
            find_info['formal'] = is_formal
        logging.info(" filter dictory result is %s"%find_info)
        result = self.mongodb.person.info.find(find_info).\
        sort([('last_update_time',-1)]).limit(size).skip(skip)
        if result == []: 
            raise DBQueryError('error when get person detail infomation by filter')
        return result

    def get_person_detail(self,person_id):
        """get missing person information by person_id

        Args:
            person_id: can be a list or a string or a objectid

        Returns:
        """
        result = []
        if type(person_id) == list:
            result =  self.mongodb.person.info.find({"_id":{"$in":person_id}}) 
        else:
            if type(person_id) != ObjectId:
                # logging.info("in filter")
                person_id = ObjectId(person_id)
            result = self.mongodb.person.info.find_one({'_id':person_id})
        if result == []or result == None:
            raise DBQueryError('error when get person detail infomation by person_id: %s'%person_id)   
        # logging.info("get person_detail result is :%s"%result)
        # result['picture_key_list'] =  eval(result['picture_key_list'])      
        return result

    def _track_info_creator(self, shoot_type, info_data, shooter_info=None):
        track_info = {}
        if shoot_type == self.CAMERA:
            track_info = {
                # 'name':info_data['name'],
                # 'sex':info_data['sex'],
                # 'age':info_data['age'],
                # 'person_'
                # 'shoot_user_id':person_id_obj,
                'pic_key':info_data['pic_key'],
                'type':self.CAMERA,
                'confidence':info_data['confidence'],
                'coordinate':info_data['coordinate'],
                'date':info_data['date'],
                'person_id':info_data['person_id']
            }
        elif shoot_type == self.PERSON:
            track_info = {
                # 'name':info_data['name'],
                # 'sex':info_data['sex'],
                # 'age':info_data['age'],
                # 'person_'
                # 'shoot_user_id':person_id_obj,
                'pic_key':info_data['pic_key'],
                'type':self.PERSON,
                'confidence':info_data['confidence'],
                'coordinate':info_data['coordinate'],
                'date':info_data['date'],
                'user_id':shooter_info['user_id'],
                'user_nick_name':shooter_info['user_nick_name'],
                'description':shooter_info['description'],
                'person_id':info_data['person_id']
            }
        elif shoot_type == self.PERSON_SEARCH:
            track_info = {
                # 'name':info_data['name'],
                # 'sex':info_data['sex'],
                # 'age':info_data['age'],
                # 'person_'
                # 'shoot_user_id':person_id_obj,
                'pic_key':info_data['pic_key'],
                'type':self.PERSON_SEARCH,
                'confidence':info_data['confidence'],
                'coordinate':info_data['coordinate'],
                'date':info_data['date'],
                'user_id':shooter_info['user_id'],
                'user_nick_name':shooter_info['user_nick_name'],
                'person_id':info_data['person_id']
            }

        return track_info


    def insert_new_track(self, shoot_type, info_data, shooter_info):
        """ Insert track list into mongodb.

        """

        track_info = self._track_info_creator(shoot_type, info_data, shooter_info)
        inserted_id = self.mongodb.tracklist.insert_one(track_info).inserted_id
        return inserted_id

    def update_person_info(self, track_id, person_id, coordinate, date):
        update_filter = {'_id':person_id}
        update_data = {
            '$push':{'track_list':track_id},
            '$set':{'last_update_spot':coordinate,'last_update_time':date},
            }
        self.mongodb.person.info.update_one(update_filter, update_data)

    # def get_tracks_detail(self, track_type, filter_info):
    #     if track_type == self.POLICE:
    #         self.mongodb.tracklist.find().sort({'_id':-1}).limit(1)

    def get_tracks_detail(self, track_id):
        """Get track detail information (both camera track and human track are ok),

        Args:
            track_id: can be a list or a ObjectId or a String.
        """
        if type(track_id) == list:
            result =  self.mongodb.tracklist.find({"_id":{"$in":track_id}})
        else:
            if type(track_id) != ObjectId:
                person_id = ObjectId(person_id)
            result = self.mongodb.tracklist.find_one({"_id":track_id})    
        if result == [] or result == None:
            raise DBQueryError('error when get track detail infomation by track_id(track_id_list)')            
        return result

    def get_track_info_by_range(self,spot, longitude, latitude):
        """get track information by range.

        Args:
            spot: the center spot, eg. [111.11,22.2]
            range_longitude: search longitude
            range_latitude: search latitude

        """
        track_info = self.mongodb.tracklist.find({
                'coordinate':{
                    '$geoWithin':{
                        '$box':[[spot[0]+latitude,spot[1]+longitude],[spot[0]-latitude,spot[1]-longitude]]
                    }
                }
            })
        return track_info
