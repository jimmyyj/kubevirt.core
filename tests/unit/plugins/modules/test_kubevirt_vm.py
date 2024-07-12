# -*- coding: utf-8 -*-
# Copyright 2023 Red Hat, Inc.
# Apache License 2.0 (see LICENSE or http://www.apache.org/licenses/LICENSE-2.0)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.kubernetes.core.plugins.module_utils.k8s import runner
from ansible_collections.kubevirt.core.plugins.modules import kubevirt_vm
from ansible_collections.kubevirt.core.tests.unit.utils.ansible_module_mock import (
    AnsibleFailJson,
    AnsibleExitJson,
    exit_json,
    fail_json,
    set_module_args,
)


def test_module_fails_when_required_args_missing(mocker):
    mocker.patch.object(AnsibleModule, "fail_json", fail_json)
    with pytest.raises(AnsibleFailJson):
        set_module_args({})
        kubevirt_vm.main()


VM_DEFINITION_CREATE = {
    "apiVersion": "kubevirt.io/v1",
    "kind": "VirtualMachine",
    "metadata": {
        "name": "testvm",
        "namespace": "default",
        "labels": {"environment": "staging", "service": "loadbalancer"},
    },
    "spec": {
        "running": True,
        "instancetype": {"name": "u1.medium"},
        "preference": {"name": "fedora"},
        "dataVolumeTemplates": [
            {
                "metadata": {"name": "testdv"},
                "spec": {
                    "source": {
                        "registry": {
                            "url": "docker://quay.io/containerdisks/fedora:latest"
                        },
                    },
                    "storage": {
                        "accessModes": ["ReadWriteOnce"],
                        "resources": {"requests": {"storage": "5Gi"}},
                    },
                },
            }
        ],
        "template": {
            "metadata": {
                "labels": {"environment": "staging", "service": "loadbalancer"}
            },
            "spec": {
                "domain": {"devices": {}},
                "terminationGracePeriodSeconds": 180,
            },
        },
    },
}

VM_DEFINITION_RUNNING = {
    "apiVersion": "kubevirt.io/v1",
    "kind": "VirtualMachine",
    "metadata": {
        "name": "testvm",
        "namespace": "default",
    },
    "spec": {
        "running": True,
        "template": {
            "spec": {
                "domain": {"devices": {}},
            },
        },
    },
}

VM_DEFINITION_STOPPED = {
    "apiVersion": "kubevirt.io/v1",
    "kind": "VirtualMachine",
    "metadata": {
        "name": "testvm",
        "namespace": "default",
    },
    "spec": {
        "running": False,
        "template": {
            "spec": {
                "domain": {"devices": {}},
            },
        },
    },
}

MODULE_PARAMS_DEFAULT = {
    "api_version": "kubevirt.io/v1",
    "annotations": None,
    "labels": None,
    "running": True,
    "instancetype": None,
    "preference": None,
    "data_volume_templates": None,
    "spec": None,
    "wait": False,
    "wait_sleep": 5,
    "wait_timeout": 5,
    "kubeconfig": None,
    "context": None,
    "host": None,
    "api_key": None,
    "username": None,
    "password": None,
    "validate_certs": None,
    "ca_cert": None,
    "client_cert": None,
    "client_key": None,
    "proxy": None,
    "no_proxy": None,
    "proxy_headers": None,
    "persist_config": None,
    "impersonate_user": None,
    "impersonate_groups": None,
    "state": "present",
    "force": False,
    "delete_options": None,
}

MODULE_PARAMS_CREATE = MODULE_PARAMS_DEFAULT | {
    "name": "testvm",
    "namespace": "default",
    "labels": {"service": "loadbalancer", "environment": "staging"},
    "instancetype": {"name": "u1.medium"},
    "preference": {"name": "fedora"},
    "data_volume_templates": [
        {
            "metadata": {"name": "testdv"},
            "spec": {
                "source": {
                    "registry": {
                        "url": "docker://quay.io/containerdisks/fedora:latest"
                    },
                },
                "storage": {
                    "accessModes": ["ReadWriteOnce"],
                    "resources": {"requests": {"storage": "5Gi"}},
                },
            },
        }
    ],
    "spec": {
        "domain": {"devices": {}},
        "terminationGracePeriodSeconds": 180,
    },
}

MODULE_PARAMS_RUNNING = MODULE_PARAMS_DEFAULT | {
    "name": "testvm",
    "namespace": "default",
    "running": True,
}

MODULE_PARAMS_STOPPED = MODULE_PARAMS_DEFAULT | {
    "name": "testvm",
    "namespace": "default",
    "running": False,
}

MODULE_PARAMS_DELETE = MODULE_PARAMS_DEFAULT | {
    "name": "testvm",
    "namespace": "default",
    "state": "absent",
    "wait": True,
}

K8S_MODULE_PARAMS_CREATE = MODULE_PARAMS_CREATE | {
    "generate_name": None,
    "resource_definition": VM_DEFINITION_CREATE,
    "wait_condition": {"type": "Ready", "status": True},
}

K8S_MODULE_PARAMS_RUNNING = MODULE_PARAMS_RUNNING | {
    "generate_name": None,
    "resource_definition": VM_DEFINITION_RUNNING,
    "wait_condition": {"type": "Ready", "status": True},
}

K8S_MODULE_PARAMS_STOPPED = MODULE_PARAMS_STOPPED | {
    "generate_name": None,
    "resource_definition": VM_DEFINITION_STOPPED,
    "wait_condition": {"type": "Ready", "status": False, "reason": "VMINotExists"},
}

K8S_MODULE_PARAMS_DELETE = MODULE_PARAMS_DELETE | {
    "generate_name": None,
    "resource_definition": VM_DEFINITION_RUNNING,
    "wait_condition": {"type": "Ready", "status": True},
}


@pytest.mark.parametrize(
    "module_params,k8s_module_params,vm_definition,method",
    [
        (
            MODULE_PARAMS_CREATE,
            K8S_MODULE_PARAMS_CREATE,
            VM_DEFINITION_CREATE,
            "create",
        ),
        (
            MODULE_PARAMS_RUNNING,
            K8S_MODULE_PARAMS_RUNNING,
            VM_DEFINITION_RUNNING,
            "update",
        ),
        (
            MODULE_PARAMS_STOPPED,
            K8S_MODULE_PARAMS_STOPPED,
            VM_DEFINITION_STOPPED,
            "update",
        ),
        (
            MODULE_PARAMS_DELETE,
            K8S_MODULE_PARAMS_DELETE,
            VM_DEFINITION_RUNNING,
            "delete",
        ),
    ],
)
def test_module(mocker, module_params, k8s_module_params, vm_definition, method):
    mocker.patch.object(AnsibleModule, "exit_json", exit_json)
    mocker.patch.object(runner, "get_api_client")

    perform_action = mocker.patch.object(
        runner,
        "perform_action",
        return_value={
            "method": method,
            "changed": True,
            "result": "success",
        },
    )

    with pytest.raises(AnsibleExitJson):
        set_module_args(module_params)
        kubevirt_vm.main()

    perform_action.assert_called_once_with(
        mocker.ANY,
        vm_definition,
        k8s_module_params,
    )


CREATE_VM_PARAMS = {
    "api_version": "kubevirt.io/v1",
    "running": True,
    "namespace": "default",
}

CREATE_VM_PARAMS_ANNOTATIONS = CREATE_VM_PARAMS | {
    "annotations": {"test": "test"},
}

CREATE_VM_PARAMS_LABELS = CREATE_VM_PARAMS | {
    "labels": {"test": "test"},
}

CREATE_VM_PARAMS_INSTANCETYPE = CREATE_VM_PARAMS | {
    "instancetype": {"name": "u1.medium"},
}

CREATE_VM_PARAMS_PREFERENCE = CREATE_VM_PARAMS | {
    "preference": {"name": "fedora"},
}

CREATE_VM_PARAMS_DATAVOLUMETEMPLATE = CREATE_VM_PARAMS | {
    "data_volume_templates": [
        {
            "metadata": {"name": "testdv"},
            "spec": {
                "source": {
                    "registry": {
                        "url": "docker://quay.io/containerdisks/fedora:latest"
                    },
                },
                "storage": {
                    "accessModes": ["ReadWriteOnce"],
                    "resources": {"requests": {"storage": "5Gi"}},
                },
            },
        },
    ],
}

CREATE_VM_PARAMS_NAME = CREATE_VM_PARAMS | {
    "name": "testvm",
}

CREATE_VM_PARAMS_GENERATE_NAME = CREATE_VM_PARAMS | {
    "generate_name": "testvm-1234",
}

CREATE_VM_PARAMS_SPECS = CREATE_VM_PARAMS | {
    "spec": {
        "domain": {
            "devices": {
                "cpu": {
                    "cores": 2,
                    "socket": 1,
                    "threads": 2,
                }
            }
        }
    }
}

CREATED_VM = {
    "apiVersion": "kubevirt.io/v1",
    "kind": "VirtualMachine",
    "metadata": {
        "namespace": "default",
    },
    "spec": {
        "running": True,
        "template": {
            "spec": {
                "domain": {
                    "devices": {},
                },
            },
        },
    },
}

CREATED_VM_LABELS = {
    "apiVersion": "kubevirt.io/v1",
    "kind": "VirtualMachine",
    "metadata": {
        "namespace": "default",
        "labels": {
            "test": "test",
        },
    },
    "spec": {
        "running": True,
        "template": {
            "metadata": {
                "labels": {"test": "test"},
            },
            "spec": {
                "domain": {
                    "devices": {},
                },
            },
        },
    },
}

CREATED_VM_ANNOTATIONS = {
    "apiVersion": "kubevirt.io/v1",
    "kind": "VirtualMachine",
    "metadata": {
        "namespace": "default",
        "annotations": {
            "test": "test",
        },
    },
    "spec": {
        "running": True,
        "template": {
            "metadata": {
                "annotations": {"test": "test"},
            },
            "spec": {
                "domain": {
                    "devices": {},
                },
            },
        },
    },
}

CREATED_VM_INSTANCETYPE = {
    "apiVersion": "kubevirt.io/v1",
    "kind": "VirtualMachine",
    "metadata": {
        "namespace": "default",
    },
    "spec": {
        "running": True,
        "instancetype": {"name": "u1.medium"},
        "template": {
            "spec": {
                "domain": {
                    "devices": {},
                },
            },
        },
    },
}

CREATED_VM_PREFERENCE = {
    "apiVersion": "kubevirt.io/v1",
    "kind": "VirtualMachine",
    "metadata": {
        "namespace": "default",
    },
    "spec": {
        "running": True,
        "preference": {"name": "fedora"},
        "template": {
            "spec": {
                "domain": {
                    "devices": {},
                },
            },
        },
    },
}

CREATED_VM_DATAVOLUMETEMPLATE = {
    "apiVersion": "kubevirt.io/v1",
    "kind": "VirtualMachine",
    "metadata": {
        "namespace": "default",
    },
    "spec": {
        "running": True,
        "dataVolumeTemplates": [
            {
                "metadata": {"name": "testdv"},
                "spec": {
                    "source": {
                        "registry": {
                            "url": "docker://quay.io/containerdisks/fedora:latest"
                        },
                    },
                    "storage": {
                        "accessModes": ["ReadWriteOnce"],
                        "resources": {"requests": {"storage": "5Gi"}},
                    },
                },
            },
        ],
        "template": {
            "spec": {
                "domain": {
                    "devices": {},
                },
            },
        },
    },
}

CREATED_VM_NAME = {
    "apiVersion": "kubevirt.io/v1",
    "kind": "VirtualMachine",
    "metadata": {
        "name": "testvm",
        "namespace": "default",
    },
    "spec": {
        "running": True,
        "template": {
            "spec": {
                "domain": {
                    "devices": {},
                },
            },
        },
    },
}

CREATED_VM_GENERATE_NAME = {
    "apiVersion": "kubevirt.io/v1",
    "kind": "VirtualMachine",
    "metadata": {
        "generateName": "testvm-1234",
        "namespace": "default",
    },
    "spec": {
        "running": True,
        "template": {
            "spec": {
                "domain": {
                    "devices": {},
                },
            },
        },
    },
}

CREATED_VM_SPECS = {
    "apiVersion": "kubevirt.io/v1",
    "kind": "VirtualMachine",
    "metadata": {
        "namespace": "default",
    },
    "spec": {
        "running": True,
        "template": {
            "spec": {
                "domain": {
                    "devices": {
                        "cpu": {
                            "cores": 2,
                            "socket": 1,
                            "threads": 2,
                        }
                    },
                },
            },
        },
    },
}


@pytest.mark.parametrize(
    "params,expected",
    [
        (CREATE_VM_PARAMS, CREATED_VM),
        (CREATE_VM_PARAMS_ANNOTATIONS, CREATED_VM_ANNOTATIONS),
        (CREATE_VM_PARAMS_LABELS, CREATED_VM_LABELS),
        (CREATE_VM_PARAMS_INSTANCETYPE, CREATED_VM_INSTANCETYPE),
        (CREATE_VM_PARAMS_PREFERENCE, CREATED_VM_PREFERENCE),
        (CREATE_VM_PARAMS_DATAVOLUMETEMPLATE, CREATED_VM_DATAVOLUMETEMPLATE),
        (CREATE_VM_PARAMS_NAME, CREATED_VM_NAME),
        (CREATE_VM_PARAMS_GENERATE_NAME, CREATED_VM_GENERATE_NAME),
        (CREATE_VM_PARAMS_SPECS, CREATED_VM_SPECS),
    ],
)
def test_create_vm(params, expected):
    assert kubevirt_vm.create_vm(params) == expected
