#!/usr/bin/env python
# -*- coding:utf-8 -*-
# author : liuyu
# date 2017
import pykube
import sys


def initconfig(k8sApiPort):
    url = "http://" + k8sApiPort
    return pykube.HTTPClient(pykube.KubeConfig.from_url(url))

api = initconfig(sys.argv[1])

def createNamespace(NamespaceName):
    obj = {
        "kind": "Namespace",
        "apiVersion": "v1",
        "metadata": {
            "name": NamespaceName
        }
    }
    print(pykube.Namespace(api, obj).create())


def deleteNamespace(NamespaceName):
    obj = {
        "kind": "Namespace",
        "apiVersion": "v1",
        "metadata": {
            "name": NamespaceName
        }
    }
    print(pykube.Namespace(api, obj).delete())


def createReplicationController(action, NamespaceName, appname, replicas, hostPath, containerPath, containerImage, cpu,
                                mem, containerPort, deployId, envname, envalue):
    # cpu = str(cpu) + 'm'
    mem = str(mem) + 'Gi'
    withLB_1 = "withLB" + deployId
    volumesName = appname + "volumes"
    rcname = appname + "-rc"
    obj = {
        "kind": "ReplicationController",
        "apiVersion": "v1",
        "metadata": {
            "name": rcname,
            "namespace": NamespaceName,
            "labels": {
                "deployId": deployId
            }
        },
        "spec": {
            "replicas": replicas,
            "selector": {
                "deployId": deployId
            },
            "template": {
                "metadata": {
                    "deletionGracePeriodSeconds": 0,
                    "labels": {
                        "deployId": deployId,
                        "version": "1",
                        withLB_1: "TRUE"
                    },
                    "annotations": {
                        "deployName": appname
                    }
                },
                "spec": {
                    "volumes": [
                        {
                            "name": volumesName,
                            "hostPath": {
                                "path": hostPath
                            }
                        }
                    ],
                    "containers": [
                        {
                            "name": appname,
                            "image": containerImage,
                            "env": [
                                {
                                    "name": "DOMEOS_SERVER_ADDR",
                                    "value": "10.23.74.210:8080"
                                },
                                {
                                    "name": "CLUSTER_NAME",
                                    "value": "domeos"
                                },
                                {
                                    "name": "NETWORK_MODE",
                                    "value": "DEFAULT"
                                },
                                {
                                    "name": "MY_POD_NAME",
                                    "valueFrom": {
                                        "fieldRef": {
                                            "apiVersion": "v1",
                                            "fieldPath": "metadata.name"
                                        }
                                    }
                                },
                                {
                                    "name": "MY_POD_NAMESPACE",
                                    "valueFrom": {
                                        "fieldRef": {
                                            "apiVersion": "v1",
                                            "fieldPath": "metadata.namespace"
                                        }
                                    }
                                },
                                {
                                    "name": "MY_POD_IP",
                                    "valueFrom": {
                                        "fieldRef": {
                                            "apiVersion": "v1",
                                            "fieldPath": "status.podIP"
                                        }
                                    }
                                },
                                {
                                    "name": "envname",
                                    "value": "envalue"
                                }
                            ],
                            "resources": {
                                "limits": {
                                    "cpu": cpu,
                                    "memory": mem
                                }
                            },
                            "volumeMounts": [
                                {
                                    "name": volumesName,
                                    "mountPath": containerPath
                                }
                            ],
                            "livenessProbe": {
                                "tcpSocket": {
                                    "port": containerPort
                                },
                                "initialDelaySeconds": 1,
                                "timeoutSeconds": 3,
                                "periodSeconds": 10,
                                "successThreshold": 1,
                                "failureThreshold": 3
                            },
                            "terminationMessagePath": "/dev/termination-log",
                            "imagePullPolicy": "Always"
                        }
                    ],
                    "restartPolicy": "Always",
                    "terminationGracePeriodSeconds": 30,
                    "dnsPolicy": "ClusterFirst",
                    "nodeSelector": {
                        "TESTENV": "HOSTENVTYPE"
                    },
                    "securityContext": {}
                }
            }
        }
    }
    if envname != "null" and envalue != "null":
        obj["spec"]["template"]["spec"]["containers"][0]["env"][
            len(obj["spec"]["template"]["spec"]["containers"][0]["env"]) - 1]["name"] = envname
        obj["spec"]["template"]["spec"]["containers"][0]["env"][
            len(obj["spec"]["template"]["spec"]["containers"][0]["env"]) - 1]["value"] = envalue
    if action == "create":
        pykube.ReplicationController(api, obj).create()
    elif action == "update":
        pykube.ReplicationController(api, obj).update()
    else:
        return 0


def deleteReplicationController(NamespaceName, appname, deployId):
    rcname = appname + "-rc"
    obj = {
        "kind": "ReplicationController",
        "apiVersion": "v1",
        "metadata": {
            "name": rcname,
            "namespace": NamespaceName,
            "labels": {
                "deployId": deployId
            }
        }
    }
    pykube.ReplicationController(api, obj).delete()


def createService(action, NamespaceName, appname, hostIP, hostPort, containerPort, loadBalancerId):
    svcname = appname + "-svc"
    withLB_1 = "withLB" + loadBalancerId
    portName = "port" + str(hostPort)
    obj = {
        "kind": "Service",
        "apiVersion": "v1",
        "metadata": {
            "name": svcname,
            "namespace": NamespaceName,
            "labels": {
                "loadBalancerId": loadBalancerId
            }
        },
        "spec": {
            "ports": [
                {
                    "name": portName,
                    "protocol": "TCP",
                    "port": hostPort,
                    "targetPort": containerPort,
                }
            ],
            "selector": {
                withLB_1: "TRUE"
            },
            "type": "NodePort",
            "externalIPs": [
                hostIP
            ],
            "deprecatedPublicIPs": [
                hostIP
            ],
            "sessionAffinity": "None"
        },
    }
    # print(json.dumps(obj, indent=4))
    if action == "create":
        pykube.Service(api, obj).create()
    elif action == "update":
        pykube.Service(api, obj).update()
    else:
        return 0

def deleteService(NamespaceName, appname):
    svcname = appname + "-svc"
    obj = {
        "apiVersion": "v1",
        "kind": "Service",
        "metadata": {
            "name": svcname,
            "namespace": NamespaceName,
        }
    }
    pykube.Service(api, obj).delete()


def getWebShellUrl(NamespaceName, appname, DomeosIPort):
    rcname = appname + "-rc"
    urls = {}
    pods = pykube.Pod.objects(api).filter(namespace=NamespaceName)
    for i in pods.response["items"]:
        if i["status"]["phase"] == "Running" and rcname in i["metadata"]["name"]:
            # http://10.23.74.210:8080/console/?host=10.23.74.213&container=8be3cd260d6c&type=CLUSTER&id=1
            urls[i["metadata"]["name"]] = "http://" + DomeosIPort + "/console?host=" + \
                                          i["status"]["hostIP"] + "&container=" + \
                                          i["status"]["containerStatuses"][0]["containerID"][9:21] + \
                                          "&type=CLUSTER&id=1"
            '''print("pod name : %s  hostip : %s  imagename : %s  webshell : %s" % (
                i["metadata"]["name"], i["status"]["hostIP"],
                i["status"]["containerStatuses"][0]["containerID"][9:21],
                urls[i["metadata"]["name"]]))'''

    return urls


def existNamespace(namespace):
    k = pykube.Namespace.objects(api).response
    for i in k["items"]:
        if i["metadata"]["name"] == namespace:
            return False
    return True


def nodeips():
    resp = pykube.Node.objects(api).response
    ips = []
    for a in resp["items"]:
        ips.append(a["status"]["addresses"][0]["address"])
    return ips

def createdocker(action, NamespaceName, appname, replicas, hostIP, hostPort, hostPath, containerPath, containerImage,
                 cpu, mem, containerPort, deployId, envname, envalue):
    if existNamespace(NamespaceName):
        createNamespace(NamespaceName)
        print("create namespace %s" % NamespaceName)
    createReplicationController(action, NamespaceName, appname, replicas, hostPath, containerPath, containerImage, cpu,
                                mem, containerPort, deployId, envname, envalue)
    createService(action, NamespaceName, appname, hostIP, hostPort, containerPort, deployId)


def updatedocker(action, NamespaceName, appname, replicas, hostIP, hostPort, hostPath, containerPath, containerImage,
                 cpu, mem, containerPort, deployId, envname, envalue):
    createNamespace(NamespaceName)
    createReplicationController(action, NamespaceName, appname, replicas, hostPath, containerPath, containerImage, cpu,
                                mem, containerPort, deployId, envname, envalue)


def deletedocker(action, NamespaceName, appname, hostPath, containerPath, containerImage, cpu, mem, containerPort,
                 deployId, envname, envalue):
    action = "update"
    replicas = 0
    createReplicationController(action, NamespaceName, appname, replicas, hostPath, containerPath, containerImage, cpu,
                                mem, containerPort, deployId, envname, envalue)
    deleteReplicationController(NamespaceName, appname, deployId)
    deleteService(NamespaceName, appname)
    if len(pykube.ReplicationController.objects(api).filter(namespace=NamespaceName).response["items"]) == 0:
        deleteNamespace(NamespaceName)



if int(len(sys.argv)) <= 1:
    print("error")
    sys.exit(100)
initconfig(sys.argv[1])

if sys.argv[2] == 'create':
    createdocker(sys.argv[2], sys.argv[3], sys.argv[4], int(sys.argv[5]),
                 sys.argv[6], int(sys.argv[7]), sys.argv[8], sys.argv[9], sys.argv[10], int(sys.argv[11]),
                 int(sys.argv[12]), int(sys.argv[13]), sys.argv[14], sys.argv[15], sys.argv[16])
elif sys.argv[2] == 'update':
    updatedocker(sys.argv[2], sys.argv[3], sys.argv[4], int(sys.argv[5]),
                 sys.argv[6], int(sys.argv[7]), sys.argv[8], sys.argv[9], sys.argv[10], int(sys.argv[11]),
                 int(sys.argv[12]), int(sys.argv[13]), sys.argv[14], sys.argv[15], sys.argv[16])
elif sys.argv[2] == 'delete':
    deletedocker(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5],
                 sys.argv[6], sys.argv[7], int(sys.argv[8]), int(sys.argv[9]), int(sys.argv[10]), sys.argv[11],
                 sys.argv[12], sys.argv[13])
elif sys.argv[2] == 'getwebshellurl':
    print(getWebShellUrl(sys.argv[3], sys.argv[4], sys.argv[5]))
elif sys.argv[2] == 'getnodeips':
    print(str(nodeips()))
else:
    print("error")
