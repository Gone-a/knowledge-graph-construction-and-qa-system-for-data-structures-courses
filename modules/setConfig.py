from config_manager import ConfigManager

"""
设置配置控制器的各种配置

conf={
    'key':'database',
    'value':{
        'database.user_name':'neo4j',
        'database.password':'123456',
        'database.uri':'bolt://localhost:7687'
    }

}

"""
def SetDatabase(conf: dict,config: ConfigManager):
    if(conf.get('key')=='database'):    
        config.set('database.user_name', conf.get('value').get('database.user_name'))
        config.set('database.password', conf.get('value').get('database.password'))
        config.set('database.uri', conf.get('value').get('database.uri'))

    if(conf.get('key')=='api'):
        config.set('api.deepseek_api_key', conf.get('value').get('api_key'))
        config.set('deepseek_model_name', conf.get('value').get('model_name'))
        config.set('api.deepseek_base_url', conf.get('value').get('base_url'))
    
    return config