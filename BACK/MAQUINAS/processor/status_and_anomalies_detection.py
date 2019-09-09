
def get_status_servers(DAO,DAO_anomalies, room_id, rack_id, server_id,initial_timestamp,end_timestamp, metrics = ["temperature", "energy", "utilization"]):
    dict_status = {}
    anomaly_type = "None"
    anomaly_value = False

    #creation of the status dict
    for metric in metrics:
        #get rack status
        dict_status[metric] = DAO.select_server_metric_by_roomAndRackAndServerIds(room_id, rack_id, server_id, initial_timestamp, end_timestamp,
                                                            metric_type=metric)
        # get anomalies
        if(not DAO_anomalies is None):
            anomaly_value_4_metric = DAO_anomalies.select_anomaly_by_roomAndRackAndServerIds(room_id, rack_id, server_id,
                                                                                    initial_timestamp,
                                                                                    end_timestamp, anomaly_type=metric)
            if(anomaly_value_4_metric): #Esto ahora mismo guarda la última pero podemos ponerlo que devuelva un array para los tipos porque podría haber varios tipos de anomalías, sino se queda con la última que sea True
                anomaly_type = metric
                anomaly_value = anomaly_value_4_metric

    dict_status["total"] = get_total_status(dict_status)
    color = color_status(dict_status["total"])

    return dict_status, color, anomaly_type, anomaly_value

#PREGUNTAR MARTA PORQUE LO DIJIMOS...
def color_status(status_total):
    if(status_total <= 50):
        color = "green"
    elif(status_total >50 and status_total<=80):
        color = "yellow"
    else:#yo aquí pondría algun color alternativo para decir que probablemente no esté operativo o a la carga que debería -> azul??
        color = "red"
    return color



def get_total_status(dict_status, minTmp = 22, maxTmp=73, minEnergy = 0, maxEnergy = 1000, minUtilization=0, maxUtilization=100):
    total = 0
    for metric in dict_status:
        if(metric=="temperature"):
            min = minTmp
            max = maxTmp
        elif(metric=="energy" or metric=="power"):
            min = minEnergy
            max = maxEnergy
        elif(metric=="utilization"):
            min = minUtilization
            max = maxUtilization
        else:
            print("ERROR EN LA MÉTRICA")
            min = 0
            max = 100
        total += 0.33 * get_percentage(dict_status[metric], min, max)
    return total


def get_percentage(value, min, max):
    return (value - min/(max-min))*100