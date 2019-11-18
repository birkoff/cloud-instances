/*jslint browser: true*/
/*global $, jQuery, alert*/

"use strict";

(function (root, $) {

    var awsDashboard = root.awsDashboard || {};

    awsDashboard = {
        allowedActions: ["stopInstance", "startInstance", "terminateInstance"],
        notRefreshStates: ["running", "stopped", "terminated"],
        instancesList: undefined,
        accountsList: undefined,
        imagesList: undefined,
        securityGroupsList: undefined,
        ownersList: undefined,
        environmentsList: undefined,
        account: undefined,
        region: undefined,
        owner: undefined,
        api: undefined,

        el: {
            // todo: fix this
            btn_control: '#instancesList button.changeStateButton',
            working_img: '<img src="images/working.gif" width="32" height="32">',
            fail_img: '<img src="images/fail.jpg">',
        },

        tmpl: {
            btn: function (btnClass, btnAction, btnCaption, instanceId, instanceName) {
                return '<button type="button" class="changeStateButton ' + btnClass + '" btnaction="' + btnAction + '" instance-id="' + instanceId + '" instance-name="' + instanceName + '">' + btnCaption + '</button>';
            },

            updateInstanceBtn: function (instanceAtt) {
                return '<button type="button" class="btn btn-outline-info btn-sm" data-toggle="modal" data-target="#update-instance-modal" data-instance-att="' + instanceAtt + '">Edit</button> ';
            },

            backupInstanceBtn: function (instanceAtt) {
                return '<button type="button" class="btn btn-outline-info btn-sm" data-toggle="modal" data-target="#backup-instance-modal" data-instance-att="' + instanceAtt + '">AMI</button> ';
            },

            alert: function (message) {
                return '<div class="alert alert-danger" role="alert">' + message + '</div>';
            },

            alert_success: function (message) {
                return '<div class="alert alert-success" role="alert">' + message + '</div>';
            },

            alert_info: function (message) {
                return '<div class="alert alert-primary" role="alert">' + message + '</div>';
            },

            datePicker: function (value) {
                return '<input class="datepicker form-control" id="update-terminate-date"  data-date-format="dd/mm/yyy" value="' + value + '" required>';
            },

            environments: function (elementId) {
                let select = '<select class="form-control" id="'+elementId+'" required>';
                let html = [select];
                awsDashboard.environmentsList.forEach(function(environment){
                    html.push("<option>" + environment + "</option>");
                });
                html.push("</select>");
                return html.join('');
            },

            owners: function (elementId) {
                let select = '<select class="form-control" id="'+elementId+'" required>';
                let html = [select, '<option></option>'];
                awsDashboard.ownersList.forEach(function(owner){
                    html.push("<option>" + owner + "</option>");
                });
                html.push("</select>");
                return html.join('');
            },

            security_groups: function () {
                let sg;
                let html = [];
                for (sg in awsDashboard.securityGroupsList) {
                    if (undefined !== awsDashboard.securityGroupsList[sg]) {
                        console.log(awsDashboard.securityGroupsList[sg]);
                        html.push("<b>" + awsDashboard.securityGroupsList[sg].id + "</b>");
                        html.push(" - " + awsDashboard.securityGroupsList[sg].name);
                        html.push("<br>");
                    }
                }
                return html.join('');
            },

            images: function () {
                let ami;
                let html = [];
                for (ami in awsDashboard.imagesList) {
                    if (undefined !== awsDashboard.imagesList[ami]) {
                        console.log("display_images: " + awsDashboard.imagesList[ami]);
                        html.push("<b>" + awsDashboard.imagesList[ami].id + "</b>");
                        html.push(" - " + awsDashboard.imagesList[ami].name);
                        html.push("<br>");
                    }
                }
                return html.join('');
            },
        },

        buttons: {
            terminateBtn: function (instanceId, instanceName) {
                return awsDashboard.tmpl.btn('btn btn-danger btn-sm', 'terminateInstance', 'Terminate', instanceId, instanceName);
            },

            startBtn: function (instanceId, instanceName) {
                return awsDashboard.tmpl.btn('btn btn-success btn-sm', 'startInstance', 'Start', instanceId, instanceName);
            },

            stopBtn: function (instanceId, instanceName) {
                return awsDashboard.tmpl.btn('btn btn-danger btn-sm', 'stopInstance', 'Stop', instanceId, instanceName);
            },

            updateBtn: function (instanceAtt) {
                return awsDashboard.tmpl.updateInstanceBtn(instanceAtt);
            },

            backupBtn: function (instanceAtt) {
                return awsDashboard.tmpl.backupInstanceBtn(instanceAtt);
            }
        },

        api_requests: {
            get_action_url: function (instanceAction) {
                let baseUrl = awsDashboard.api;
                let commonArgs = "?account=" + awsDashboard.account + "&region=" + awsDashboard.region;

                if ('listAmis' === instanceAction) {
                    return baseUrl + "/amis" + commonArgs;
                }

                if ('listSecurityGroups' === instanceAction) {
                    return baseUrl + "/securitygroups" + commonArgs;
                }

                if ('createInstance' === instanceAction) {
                    return baseUrl + "/instance";
                }

                if ('createPlatform' === instanceAction) {
                    return baseUrl + "/platform";
                }

                if ('stopInstance' === instanceAction) {
                    return baseUrl + "/instance/stop";
                }

                if ('startInstance' === instanceAction) {
                    return baseUrl + "/instance/start";
                }

                if ('updateInstance' === instanceAction) {
                    return baseUrl + "/instance";
                }

                if ('terminateInstance' === instanceAction) {
                    return baseUrl + "/instance/terminate";
                }

                if ('getInfo' === instanceAction) {
                    return baseUrl + "/info" + commonArgs;
                }

                if ('listInstances' === instanceAction) {
                    if (undefined !== awsDashboard.owner) {
                        commonArgs = commonArgs + "&owner=" + awsDashboard.owner;
                    }
                    return baseUrl + "/instances" + commonArgs;
                }

                if ('listAccounts' === instanceAction) {
                    return baseUrl + "/accounts";
                }

                if ('backupInstance' == instanceAction) {
                    return baseUrl + "/image"
                }
            },

            get_request_headers: function () {
                let api_key = $('#api_key').val();
                return {'Accept': 'application/json', 'x-api-key': api_key};
            },

            list_accounts: function() {
                let self = this;
                $.ajax({
                    type: 'GET',
                    url: self.get_action_url('listAccounts'),
                    headers: self.get_request_headers(),
                    dataType: 'json',
                    async: true
                }).done(function (data) {
                    console.log(data);
                    awsDashboard.accountsList = data;
                    awsDashboard.render_accounts();
                }).fail(function (error) {
                    console.log("An error" + error.responseText);
                    $('#invalid-feedback').append("Error listing accounts");
                });
                return
            },

            get_info: function() {
                let self = this;
                $.ajax({
                    type: 'GET',
                    url: self.get_action_url('getInfo'),
                    headers: self.get_request_headers(),
                    dataType: 'json',
                    async: true
                }).done(function (data) {
                    awsDashboard.ownersList = data.users;
                    awsDashboard.environmentsList = data.environments;
                    console.log(data);
                }).fail(function (error) {
                    console.log("An error" + error.responseText);
                    awsDashboard.ownersList = ['Error looking for users'];
                    awsDashboard.environmentsList = ['Error looking for environments'];
                    $('#invalid-feedback').append("Error looking for users<br>Error looking for environments");
                });
                return
            },

            list_amis: function() {
                let self = this;
                $.ajax({
                    type: 'GET',
                    url: self.get_action_url('listAmis'),
                    headers: self.get_request_headers(),
                    dataType: 'json',
                    async: true
                }).done(function (data) {
                    awsDashboard.imagesList = data;
                    console.log(awsDashboard.imagesList);
                }).fail(function (error) {
                    console.log(error.responseText);
                    awsDashboard.imagesList = ['Error looking for AMIs'];
//                    $('#invalid-feedback').html.append("Error looking for AMIs");
                });
                return
            },

            list_securitygroups: function () {
                let self = this;
                $.ajax({
                    type: 'GET',
                    url: self.get_action_url('listSecurityGroups'),
                    headers: self.get_request_headers(),
                    dataType: 'json',
                    async: true
                }).done(function (data) {
                    awsDashboard.securityGroupsList = data;
                    console.log(awsDashboard.securityGroupsList);
                }).fail(function (error) {
                    console.log(error.responseText);
                    awsDashboard.securityGroupsList = ['Error looking for Security Groups'];
//                    $('#invalid-feedback').html.append("Error looking for Security Groups");
                });
                return
            },

            list_instances: function () {
                let self = this;
                $.ajax({
                    type: 'GET',
                    url: self.get_action_url('listInstances'),
                    headers: self.get_request_headers(),
                    dataType: 'json',
                    async: false
                }).done(function (data) {
                    awsDashboard.instancesList = data;
                    console.log(awsDashboard.instancesList);
                    awsDashboard.render_instances();
                    //$("#wait").css("display", "none");
                }).fail(function(error) {
                    console.log(error.responseText);
                    awsDashboard.instancesList = ['Error looking for Instances'];
//                    $('#invalid-feedback').html.append("Oh No! An error searching for ec2 instances");
                    $('#instancesList').html("<h3>Oh No! An error searching for ec2 instances</h3><br>" + awsDashboard.el.fail_img);
                });
            },

            change_state: function(instanceAction, postData) {
                let self = this;
                $('#success-feedback').html(awsDashboard.tmpl.alert_info(instanceAction + " " + JSON.stringify(postData)));
                $.ajax({
                    type: 'POST',
                    url: self.get_action_url(instanceAction),
                    headers: self.get_request_headers(),
                    dataType: 'json',
                    data: JSON.stringify(postData)
                }).done(function (data) {
                    $('#success-feedback').html(awsDashboard.tmpl.alert_success(data));
                    console.log(data);
                    awsDashboard.api_requests.list_instances();
                }).fail(function (error) {
                    console.log(error.responseText);
                    $('#error-feedback').html(awsDashboard.tmpl.alert(error.responseText));
                });
                return
            },

            create_platform: function (postData) {
                let self = this;
                $('#success-feedback').html(awsDashboard.tmpl.alert_info("Creating Instance " + JSON.stringify(postData)));
                $.ajax({
                    type: 'POST',
                    url: self.get_action_url('createPlatform'),
                    headers: self.get_request_headers(),
                    dataType: 'json',
                    data: JSON.stringify(postData)
                }).done(function (data) {
                    console.log("Create Platform: " + data);
                    $('.alert').alert();
                    $('#success-feedback').html(awsDashboard.tmpl.alert_success(JSON.stringify(data)));
                    $('#create-platform').replaceWith('<button type="submit" class="btn btn-primary" id="create-platform">Submit</button>');
                    $('#create-platform-modal').modal('toggle');
                    // $('#tag-name').val("Owner");
                    // $('#tag-value').val(postData.owner);
                    $('#error-feedback-create').html("");
                    awsDashboard.api_requests.list_instances();
                }).fail(function (error) {
                    console.log(error.responseText);
                    $('#create-platform').replaceWith('<button type="submit" class="btn btn-primary" id="create-platform">Submit</button>');
                    $('#error-feedback-create').html(awsDashboard.tmpl.alert(error.responseText));
                });
            },

            create_instance: function (postData) {
                let self = this;
                $('#success-feedback').html(awsDashboard.tmpl.alert_info("Creating Instance " + JSON.stringify(postData)));
                $.ajax({
                    type: 'POST',
                    url: self.get_action_url('createInstance'),
                    headers: self.get_request_headers(),
                    dataType: 'json',
                    data: JSON.stringify(postData)
                }).done(function (data) {
                    console.log("Create Instance: " + data);
                    $('.alert').alert();
                    $('#success-feedback').html(awsDashboard.tmpl.alert_success(JSON.stringify(data)));
                    $('#create-instance').replaceWith('<button type="submit" class="btn btn-primary" id="create-instance">Submit</button>');
                    $('#create-instance-modal').modal('toggle');
                    $('#tag-name').val("Owner");
                    $('#tag-value').val(postData.owner);
                    $('#error-feedback-create').html("");
                    awsDashboard.api_requests.list_instances();
                }).fail(function (error) {
                    console.log(error.responseText);
                    $('#create-instance').replaceWith('<button type="submit" class="btn btn-primary" id="create-instance">Submit</button>');
                    $('#error-feedback-create').html(awsDashboard.tmpl.alert(error.responseText));
                });
            },

            update_instance: function (postData) {
                let self = this;
                $('#success-feedback').html(awsDashboard.tmpl.alert_info("Updating Instance " + JSON.stringify(postData)));
                $.ajax({
                    type: 'PUT',
                    url: self.get_action_url('updateInstance'),
                    headers: self.get_request_headers(),
                    dataType: 'json',
                    data: JSON.stringify(postData)
                }).done(function (data) {
                    console.log("Update Instance: " + data);
                    $('.alert').alert();
                    $('#success-feedback').html(awsDashboard.tmpl.alert_success(JSON.stringify(data)));
                    $('#update-instance').replaceWith('<button type="submit" class="btn btn-primary" id="update-instance">Submit</button>');
                    $('#update-instance-modal').modal('toggle');
                    $('#tag-name').val("Owner");
                    $('#tag-value').val(postData.owner);
                    awsDashboard.api_requests.list_instances();
                }).fail(function (error) {
                    console.log(error.responseText);
                    $('#update-instance').replaceWith('<button type="submit" class="btn btn-primary" id="update-instance">Submit</button>');
                    $('#error-feedback-update').html(awsDashboard.tmpl.alert(error.responseText));

                });
            },

            backup_instance: function (postData) {
                let self = this;
                $('#success-feedback').html(awsDashboard.tmpl.alert_info("Backing up Instance " + JSON.stringify(postData)));
                $.ajax({
                    type: 'POST',
                    url: self.get_action_url('backupInstance'),
                    headers: self.get_request_headers(),
                    dataType: 'json',
                    data: JSON.stringify(postData)
                }).done(function (data) {
                    console.log("Backup Instance: " + data);
                    $('.alert').alert();
                    $('#success-feedback').html(awsDashboard.tmpl.alert_success(JSON.stringify(data)));
                    $('#backup-instance').replaceWith('<button type="submit" class="btn btn-primary" id="backup-instance">Submit</button>');
                    $('#backup-instance-modal').modal('toggle');
                    // $('#tag-name').val("Owner");
                    // $('#tag-value').val(postData.owner);
                    // awsDashboard.api_requests.list_instances();
                }).fail(function (error) {
                    console.log(error.responseText);
                    $('#backup-instance').replaceWith('<button type="submit" class="btn btn-primary" id="backup-instance">Submit</button>');
                    $('#error-feedback-update').html(awsDashboard.tmpl.alert(error.responseText));

                });
            },
        },

        validate: {
            subdomain_name: function (subdomain_name) {
                let re = /[^a-zA-Z0-9\-]/;
                return !re.test(subdomain_name);
            },
        },

        init: function () {
            let self = this;
            self.loading();
            self.set_account();
            self.render_instances();
            self.binding_actions();
            setInterval(function () {
                self.reload();
            }, 10000);
        },

        loading: function () {
            $("#wait").css("display", "block");

            $(document).ajaxStart(function () {
                window.ajaxWorking = true;
            });

            $(document).ajaxComplete(function () {
                window.ajaxWorking = false;
            });
        },

        set_account: function () {
            let hostname = window.location.hostname;
            let sPageURL = window.location.search.substring(1);
            let sURLVariables = sPageURL.split('&');
            let params = {};
            let html = [];

            let baseUrl = 'https://000000000000.execute-api.eu-central-1.amazonaws.com/dev';
            if ("ec2manager.app" === hostname) { 
                baseUrl = 'https://111111111111.execute-api.eu-central-1.amazonaws.com/prod';
            }

            awsDashboard.api = baseUrl;

            for (let i = 0; i < sURLVariables.length; i++) {
                let sParameterName = sURLVariables[i].split('=');
                params[sParameterName[0]] = sParameterName[1];
            }

            if (undefined == params['account'] || undefined == params['region'] ) {
                $('#main-container').removeClass('container-fluid').addClass('container');
                $('#instanceModalButton').toggle(false);
                $('#platformModalButton').toggle(false);
                $('#instances-meta').html('AWS Accounts');
                awsDashboard.api_requests.list_accounts();
                throw new Error('No Error, Just stopping execution');
            }

            awsDashboard.account = params['account'];
            awsDashboard.region = params['region'];

            html.push('AWS Account: ' + awsDashboard.account + ', Region:  ' + awsDashboard.region);

            if (undefined !== params['owner']) {
                awsDashboard.owner = params['owner'];
                html.push('Owner: ' + awsDashboard.owner);
            }

            html = html.join('');
            $('#main-container').removeClass('container').addClass('container-fluid');
            $('#instanceModalButton').toggle(true);
            $('#platformModalButton').toggle(true);
            $('#instances-meta').html(html);
            awsDashboard.fetch_api_init_data();
        },

        fetch_api_init_data: function () {
            if (undefined === awsDashboard.ownersList || undefined === awsDashboard.environmentsList) {
                awsDashboard.api_requests.get_info();
            }

            if (undefined === awsDashboard.securityGroupsList) {
                awsDashboard.api_requests.list_securitygroups();
            }

            if (undefined === awsDashboard.imagesList) {
                awsDashboard.api_requests.list_amis();
            }

            if (undefined === awsDashboard.instancesList) {
                awsDashboard.api_requests.list_instances();
            }
        },

        render_accounts: function () {
            let html = [];
            html.push('<table class="table table-striped table-hover"><thead><tr>');
            html.push('<th>Account Name</th>');
            html.push('<th>Region</th>');
            html.push('<th>URL</th>');
            html.push('</tr></thead><tbody>');

            $(awsDashboard.accountsList).each(function (index, acc_item) {
                let name = acc_item.name;
                for (var region in acc_item.regions) {
                    html.push('<tr>');
                    html.push('<td>'+name+'</td>');
                    html.push('<td>'+region+'</td>');
                    html.push('<td><a href="?account='+name+'&region='+region+'">?account='+name+'&amp;region='+region+'</a></td>');
                    html.push('</tr>');
                }
            });
            html.push('</tbody></table>');
            html = html.join('');
            $("#wait").css("display", "none");
            $('#instancesList').html(html);
        },

        render_instances: function () {
            let self = this;
            let html = [];

            html.push('<table class="table table-striped table-hover"><thead><tr>');
            html.push('<th>#</th>');
            html.push('<th>Instance Name/Endpoints</th>');
            html.push('<th>Owner</th>');
            html.push('<th>Environment</th>');
            html.push('<th>Started</th>');
            html.push('<th>Type</th>');
            html.push('<th>Private IP</th>');
            html.push('<th>Public IP</th>');
            html.push('<th>State</th>');
            html.push('<th>Attributes</th>');
            html.push('<th>Actions</th>');
            html.push('</tr></thead><tbody>');

            $(awsDashboard.instancesList).each(function (index, item) {
                let currentDate = new Date(),
                    day = currentDate.getDate(),
                    month = currentDate.getMonth() + 1,
                    year = currentDate.getFullYear(),
                    now = '',
                    launch_date = item.launch_time,
                    updateInstanceBtnObject,
                    backupInstanceBtnObject,
                    terminate_on = '',
                    access,
                    offhours = '',
                    attributes = '',
                    terminateBtnObject,
                    startBtnObject,
                    btnObject,
                    stopBtnObject;

                day = (day < 10) ? '0' + day : day;
                month = (month < 10) ? '0' + month : month;
                now = day + "/" + month + "/" + year;

                let public_endpoint = '';
                let private_endpoint = (item.private_dns) ? item.private_dns : item.private_ip;

                let instance_name = '';
                if (item.state == 'running') {
                    public_endpoint = (item.public_dns) ? item.public_dns : item.public_ip;
                    public_endpoint = 'public: <a target="_blank" href="https://' + public_endpoint + '">' + public_endpoint + '</a>';
                    private_endpoint = 'private: <a target="_blank" href="https://' + private_endpoint + '">' + private_endpoint + '</a>';
                    instance_name = item.name + "<br>" + private_endpoint + "<br>" + public_endpoint;
                } else {
                    instance_name = item.name;
                }
                html.push('<tr>');
                html.push('<td>' + (parseInt(index, 10) + 1 ) + '</td>');
                html.push('<td>' + instance_name + '</td>');
                html.push('<td>' + item.owner + '</td>');
                html.push('<td>' + item.environment + '</td>');
                html.push('<td>' + launch_date + '</td>');
                html.push('<td>' + item.type + '</td>');
                html.push('<td>' + item.private_ip + '</td>');
                html.push('<td>' + item.public_ip + '</td>');

                var at_dt = '';
                if (item.state === 'stopped' && item.last_stop_at) {
                        at_dt = '<br/>at ' + item.last_stop_at;
                } else if (item.state === 'terminated' && item.terminate_date) {
                        at_dt = '<br/>at ' + item.terminate_date;
                }
                html.push('<td>' + item.state + at_dt + '</td>');

                offhours = item.stop_time === undefined ?  'stops at: <span class="badge badge-danger">FullTime</span>' : 'stops at: ' + item.stop_time + 'hrs (UTC)';
                if (undefined !== item.terminate_date) {
                    if (item.terminate_date === now) {
                        terminate_on = 'terminate: <span class="badge badge-warning">today</span>';
                    } else {
                        terminate_on = 'terminate: <span class="badge badge-success">' + item.terminate_date + '</span>';
                    }
                } else {
                    terminate_on = 'terminate: <span class="badge badge-danger">Never</span>';
                }
                attributes = offhours + '<br>' + terminate_on;
                html.push('<td>' + attributes + '</td>');

                let itemAtt = JSON.stringify(item);
                itemAtt = itemAtt.replace(/"/g, "'");
                updateInstanceBtnObject = self.buttons.updateBtn(itemAtt);
                backupInstanceBtnObject = self.buttons.backupBtn(itemAtt);

                /**
                 * Action Buttons
                 */
                switch (item.state) {
                    case 'running':
                        stopBtnObject = self.buttons.stopBtn(item.id, item.name);
                        html.push('<td class="text-left">' + updateInstanceBtnObject + backupInstanceBtnObject + stopBtnObject + '</td></tr>');
                        break;
                    case 'stopped':
                        startBtnObject = self.buttons.startBtn(item.id, item.name);
                        html.push('<td class="text-left">' + updateInstanceBtnObject + backupInstanceBtnObject + startBtnObject);
                        terminateBtnObject = self.buttons.terminateBtn(item.id, item.name);
                        html.push(' ' + terminateBtnObject + '</td></tr>');
                        break;
                    case 'terminated':
                        btnObject = '-';
                        html.push('<td class="text-left">' + btnObject + '</td></tr>');
                        break;
                    default:
                        btnObject = self.el.working_img;
                        html.push('<td class="text-left">' + updateInstanceBtnObject + backupInstanceBtnObject + btnObject + '</td></tr>');
                }
            });

            html.push('</tbody></table>');
            html = html.join('');
            $("#wait").css("display", "none");
            $('#instancesList').html(html);
        },

        binding_actions: function () {
            var self = this;

            window.addEventListener('load', function () {
                // Fetch all the forms we want to apply custom Bootstrap validation styles to
                var forms = document.getElementsByClassName('needs-validation');
                Array.prototype.filter.call(forms, function (form) {
                    form.addEventListener('submit', function (event) {
                        if (form.checkValidity() === false) {
                            event.preventDefault();
                            event.stopPropagation();
                        }
                        form.classList.add('was-validated');
                    }, false);
                });
            }, false);

            $(document).on("click", this.el.btn_control, function () {
                let instanceId = $(this).attr('instance-id'),
                    instanceName = $(this).attr('instance-name'),
                    instanceAction = $(this).attr('btnaction'),
                    actionAllowed = (self.allowedActions.indexOf(instanceAction) > -1),
                    actionConfirmed = confirm("Confirm Action: " + instanceAction + " on Instance: " + instanceName),
                    postData = {
                        id: instanceId,
                        account: awsDashboard.account,
                        region: awsDashboard.region,
                    };

                if (actionConfirmed && instanceId && actionAllowed) {
                    console.log("Action: " + instanceAction + " on Instance: " + instanceId);
                    $(this).parent('td').html(self.el.working_img);
                    self.api_requests.change_state(instanceAction, postData);
                }
            });

            $(document).on("click", "#filter-instances", function () {
                console.log(location.search);
                var owner = $('#tag-value').val();

                let sPageURL = window.location.search.substring(1);
                let sURLVariables = sPageURL.split('&');
                let params = {};
                for (let i = 0; i < sURLVariables.length; i++) {
                    let sParameterName = sURLVariables[i].split('=');
                    params[sParameterName[0]] = sParameterName[1];
                }

                var nl = window.location.pathname + '?account=' + params['account']+ '&region='+params['region']+'&owner='+owner;
                console.log(nl);
                window.location.href = nl;
//              window.location.assign(nl);
            });

            $('#create-platform-modal').on('show.bs.modal', function (event) {
                if (event.relatedTarget === undefined) {
                    return false;
                }

                let modal = $(this);

                modal.find('.datepicker').datepicker({
                    format: 'dd/mm/yyyy',
                    todayBtn: true,
                    todayHighlight: true,
                    startDate: '0d',
                    endDate: '+90d'
                });

                var today = new Date();
                var dd = today.getDate();
                var mm = today.getMonth() + 1; //January is 0!
                var yyyy = today.getFullYear();
                var utchours = today.getUTCHours();

                if (dd < 10) {
                    dd = '0' + dd;
                }
                if (mm < 10) {
                    mm = '0' + mm;
                }
                var today = dd + '/' + mm + '/' + yyyy;

                modal.find('.datepicker').val(today);
                // Replace Elements
                modal.find('#create-platform-owner').replaceWith(awsDashboard.tmpl.owners('create-platform-owner'));
                modal.find('#create-platform-environment').replaceWith(awsDashboard.tmpl.environments('create-platform-environment'));

                // Add Help Text
                modal.find('#create-platform-image-id-help').html(awsDashboard.tmpl.images());
                modal.find('#create-platform-security-groups-help').html(awsDashboard.tmpl.security_groups());
                modal.find('.current-utc-hour').replaceWith(utchours);
                modal.show();
                // event.preventDefault();
            });

            $(document).on("submit", "#create-platform-form", function () {
                let instanceName = $('#create-platform-name').val(),
                    instanceSecurityGroups = ($('#SecurityGroups').val().length) ? $('#SecurityGroups').val().split(",") : [],
                    postData = {
                        'name': instanceName,
                        "image_id": $('#create-platform-image-id').val(),
                        "platform": {
                            "username": $('#create-platform-username').val(),
                            "password": $('#create-platform-password').val(),
                            "email": $('#create-platform-email').val(),
                            "api_version": $('#create-platform-api-version').val(),
                            "ui_version": $('#create-platform-ui-version').val()
                        },
                        "owner": $('#create-platform-owner').val(),
                        "environment": $('#create-platform-environment').val(),
                        "type": $('#create-platform-type').val(),
                        "security_groups": instanceSecurityGroups,
                        "terminate_date": $('#create-platform-terminate-date').val(),
                        'terminate_time': $('#create-platform-terminate-time').val(),
                        'stop_time': $('#create-platform-stop-time').val(),
                        'start_time': $('#create-platform-start-time').val(),
                        "account": awsDashboard.account,
                        "region": awsDashboard.region,
                    };

                if (!awsDashboard.validate.subdomain_name(instanceName)) {
                    console.log("Invalid Instance Name");
                    $('#invalid-feedback').html(awsDashboard.tmpl.alert('Invalid Instance Name, Only alphanumeric charts and -'));
                    return false;
                }
                $('#success-feedback').html("Creating Instance...<br>" + self.el.working_img);
                $('#create-platform').replaceWith('<div id="create-platform">' + self.el.working_img + '</div>');
                self.api_requests.create_platform(postData);
                return false;
            });

            $('#create-instance-modal').on('show.bs.modal', function (event) {
                if (event.relatedTarget === undefined) {
                    return false;
                }

                let modal = $(this);

                modal.find('.datepicker').datepicker({
                    format: 'dd/mm/yyyy',
                    todayBtn: true,
                    todayHighlight: true,
                    startDate: '0d',
                    endDate: '+90d'
                });

                var today = new Date();
                var dd = today.getDate();
                var mm = today.getMonth() + 1; //January is 0!
                var yyyy = today.getFullYear();
                var utchours = today.getUTCHours();

                if (dd < 10) {
                    dd = '0' + dd;
                }
                if (mm < 10) {
                    mm = '0' + mm;
                }
                var today = dd + '/' + mm + '/' + yyyy;

                modal.find('.datepicker').val(today);
                // Replace Elements
                modal.find('#create-owner').replaceWith(awsDashboard.tmpl.owners('create-owner'));
                modal.find('#create-environment').replaceWith(awsDashboard.tmpl.environments('create-environment'));

                // Add Help Text
                modal.find('#create-image-id-help').html(awsDashboard.tmpl.images());
                modal.find('#create-security-groups-help').html(awsDashboard.tmpl.security_groups());
                modal.find('.current-utc-hour').replaceWith(utchours);
                modal.show();
                // event.preventDefault();
            });

            $(document).on("submit", "#create-instance-form", function () {
                let instanceName = $('#create-name').val(),
                    instanceSecurityGroups = ($('#SecurityGroups').val().length) ? $('#SecurityGroups').val().split(",") : [],
                    postData = {
                        'name': instanceName,
                        "image_id": $('#create-image-id').val(),
                        "owner": $('#create-owner').val(),
                        "environment": $('#create-environment').val(),
                        "type": $('#create-type').val(),
                        "security_groups": instanceSecurityGroups,
                        "terminate_date": $('#create-terminate-date').val(),
                        'terminate_time': $('#create-terminate-time').val(),
                        'stop_time': $('#create-stop-time').val(),
                        'start_time': $('#create-start-time').val(),
                        "account": awsDashboard.account,
                        "region": awsDashboard.region,
                    };

                if (!awsDashboard.validate.subdomain_name(instanceName)) {
                    console.log("Invalid Instance Name");
                    $('#invalid-feedback').html(awsDashboard.tmpl.alert('Invalid Instance Name, Only alphanumeric charts and -'));
                    return false;
                }
                $('#success-feedback').html("Creating Instance...<br>" + self.el.working_img);
                $('#create-instance').replaceWith('<div id="create-instance">' + self.el.working_img + '</div>');
                self.api_requests.create_instance(postData);
                return false;
            });

            $('#update-instance-modal').on('show.bs.modal', function (event) {
                if (event.relatedTarget === undefined) {
                    return false;
                }

                let button = $(event.relatedTarget),
                    instance = button.data('instance-att'),
                    modal = $(this),
                    datePicker = '',
                    team = $('#team').val();

                let itemAtt = instance.replace(/'/g, '"');
                console.log(itemAtt);
                let item = JSON.parse(itemAtt);

                modal.off("submit");
                console.log(event.relatedTarget);

                // datePicker = awsDashboard.tmpl.datePicker(item.terminate_date);
                // modal.find('#update-terminate-date').replaceWith(datePicker);
                $('.datepicker').datepicker({
                    format: 'dd/mm/yyyy',
                    todayBtn: true,
                    todayHighlight: true,
                    startDate: '0d',
                    endDate: '+90d'
                });
                modal.find('.datepicker').val(item.terminate_date);

                let sp = item.name.indexOf(".");
                let name = item.name.substring(0, sp);
                modal.find('#update-name').val(name);
                modal.find('#update-image').val(item.image_id);
                modal.find('#update-owner').val(item.owner);
                modal.find('#update-environment').val(item.environment);
                modal.find('#update-type').val(item.type);

                modal.find('#update-stop-time').val(item.stop_time);
                modal.find('#update-start-time').val(item.start_time);

                // modal.find('#update-terminate-date').val(item.terminate_date);
                modal.find('#update-terminate-time').val(item.terminate_time);

                modal.find('#update-instance-modal-label').text('Update instance ');
                modal.find('#tag-key').html('tagKey');
                // modal.find('#modal-command').html("");
                modal.show();

                modal.on("submit", "#update-instance-form", function (e) {
                    $('#update-instance').replaceWith('<div id="update-instance">'+self.el.working_img+'</div>');
                    e.preventDefault();
                    let postData = {
                        id: item.id,
                        image_id: modal.find('#update-image').val(),
                        account: awsDashboard.account,
                        region: awsDashboard.region,
                        name:  modal.find('#update-name').val(),
                        owner: modal.find('#update-owner').val(),
                        environment: modal.find('#update-environment').val(),
                        type: modal.find('#update-type').val(),
                        terminate_date: modal.find('#update-terminate-date').val(),
                        terminate_time: modal.find('#update-terminate-time').val(),
                        stop_time: modal.find('#update-stop-time').val(),
                        start_time: modal.find('#update-start-time').val()
                    };
                    self.api_requests.update_instance(postData);
                    return false;
                });

                // return false;
            });

            $('#backup-instance-modal').on('show.bs.modal', function (event) {
                if (event.relatedTarget === undefined) {
                    return false;
                }
                let button = $(event.relatedTarget);

                let instance = button.data('instance-att');

                let itemAtt = instance.replace(/'/g, '"');
                console.log(itemAtt);
                let item = JSON.parse(itemAtt);
                let modal = $(this);

                modal.off("submit");
                console.log(event.relatedTarget);

                modal.find('#image-instance-name').val(item.name);
                modal.find('#image-owner').val(item.owner);

                modal.show();

                modal.on("submit", "#backup-instance-form", function (e) {
                    $('#backup-instance').replaceWith('<div id="backup-instance">'+self.el.working_img+'</div>');
                    e.preventDefault();
                    let postData = {
                        id: item.id,
                        account: awsDashboard.account,
                        region: awsDashboard.region,
                        image_name:  modal.find('#image-name').val(),
                        owner: modal.find('#image-owner').val(),
                    };
                    self.api_requests.backup_instance(postData);
                    return false;
                });

            });
        },

        reload: function () {
            if (window.ajaxWorking === true) {
                return;
            }
            if (!this.instancesList) {
                awsDashboard.api_requests.list_instances();
                return;
            }
            let instance;
            for (instance in this.instancesList) {
                if (this.instancesList.hasOwnProperty(instance) && this.notRefreshStates.indexOf(this.instancesList[instance].state) <= -1) {
                    awsDashboard.api_requests.list_instances();
                    return;
                }
            }
            $('#success-feedback').html('');
            // $('#error-feedback').html('');
        }
    };
    awsDashboard.init();

}(window, jQuery));
