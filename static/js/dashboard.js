$(document).ready(function () {
   
    // Fetch levels based on season selection
    $('#season').change(function () {
        const season = $(this).val();
        if (season) {
            $.get(`/gamefetcher/get_levels/${season}`, function (data) {
                let levelOptions = '<option value="">Valitse taso</option>';
                data.forEach(function (level) {
                    levelOptions += `<option value="${level.LevelID}">${level.LevelName}</option>`;
                });
                $('#levels').html(levelOptions);
                $('#statgroups').html('<option value="">Valitse sarja/lohko</option>');
                $('#teams').html('<option value="">Valitse joukkueet</option>');
            });
        }
    });

    // Trigger change to pre-populate levels when the page loads
    $('#season').trigger('change');

    // Fetch stat groups based on level selection
    $('#levels').change(function () {
        const levelId = $(this).val();
        const season = $('#season').val();
        if (levelId) {
            $.get(`/gamefetcher/get_statgroups/${season}/${levelId}/0`, function (data) {
                let statGroupOptions = '<option value="">Valitse sarja/lohko</option>';
                data.forEach(function (statGroup) {
                    statGroupOptions += `<option value="${statGroup.StatGroupID}">${statGroup.StatGroupName}</option>`;
                });
                $('#statgroups').html(statGroupOptions);
                $('#teams').html('<option value="">Valitse joukkueet</option>');
            });
        }
    });

    // Fetch teams based on stat group selection
    $('#statgroups').change(function () {
        const statGroupId = $(this).val();
        const season = $('#season').val();
        let selectedStatGroupName = $('#statgroups option:selected').text(); // Get selected stat group name
    
        if (statGroupId) {
            $.get(`/gamefetcher/get_teams/${season}/${statGroupId}`, function (data) {
                if (Array.isArray(data.Teams)) {
                    let teamOptions = '';
                    
                    // Generate each <option> with the necessary data attributes
                    data.Teams.forEach(function (team) {
                        teamOptions += `<option value="${team.TeamID}" 
                                        data-abbrv="${team.TeamAbbrv || ''}" 
                                        data-association="${team.TeamAssociation || ''}" 
                                        data-img="${team.TeamImg || ''}"
                                        data-name="${team.TeamAbbrv || ''}" 
                                        data-statgroup="${selectedStatGroupName || ''}">
                                        ${team.TeamAbbrv}</option>`;
                    });
                        
                    // Populate the teams dropdown
                    $('#teams').html(teamOptions);
                }
            });
        }
    });
    
    
    $('#dashboardForm').submit(function (e) {
        e.preventDefault();

        const selectedTeams = [];
        const action = $(document.activeElement).val();

        $('#teams option:selected').each(function () {
            selectedTeams.push({
                TeamID: $(this).val(),
                TeamAbbrv: $(this).data('abbrv'),
                team_association: $(this).data('association'),
                team_name: $(this).data('name'),
                stat_group: $(this).data('statgroup')
            });
        });

        const data = {
            action: action,
            teams: selectedTeams,
            season: $('#season').val(),
            level_id: $('#levels').val(),
            statgroup: $('#statgroups').val()
        };

        $.ajax({
            url: '/dashboard/update_teams',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(data),
            success: function (response) {

                // Update the managed teams list
                const managedTeamsList = $('#managedTeamsList');
                managedTeamsList.empty();  // Clear current list
                response.managed_teams.forEach(team => {
                    managedTeamsList.append(`
                        <li data-team-id="${team.team_id}">
                            ${team.team_name} (${team.stat_group})
                        </li>
                    `);
                });


                // Update the followed teams list
                const followedTeamsList = $('#followedTeamsList');
                followedTeamsList.empty();  // Clear current list
                response.followed_teams.forEach(team => {
                    followedTeamsList.append(`
                        <li data-team-id="${team.team_id}">
                            ${team.team_name} (${team.stat_group})
                        </li>
                    `);
                });
                updateRemoveTeamsModal(response.managed_teams, response.followed_teams);

            },
            error: function (xhr) {
                alert('An error occurred: ' + xhr.responseText);
            }
        });
    });

     // Function to update Remove Teams Modal content
    function updateRemoveTeamsModal(managedTeams, followedTeams) {
        const managedTeamsModalList = $('#removeTeamsModal .modal-body ul:first');
        const followedTeamsModalList = $('#removeTeamsModal .modal-body ul:last');

        managedTeamsModalList.empty();
        managedTeams.forEach(team => {
            managedTeamsModalList.append(`
                <li>
                    <input type="checkbox" name="teams" value="${team.team_id}" data-relationship="manage">
                    ${team.team_name} (Stat Group: ${team.stat_group})
                </li>
            `);
        });

        followedTeamsModalList.empty();
        followedTeams.forEach(team => {
            followedTeamsModalList.append(`
                <li>
                    <input type="checkbox" name="teams" value="${team.team_id}" data-relationship="follow">
                    ${team.team_name} (Stat Group: ${team.stat_group})
                </li>
            `);
        });
    }


    // Handle remove teams confirmation
    $('#confirmRemoveTeams').click(function () {
        const selectedTeams = [];
        
        // Collect selected teams with their relationship type
        $('#removeTeamsForm input[name="teams"]:checked').each(function () {
            selectedTeams.push({
                team_id: $(this).val(),
                relationship_type: $(this).data('relationship')
            });
        });

        // Send the selected teams to the server
        $.ajax({
            url: '/dashboard/remove_teams',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ teams: selectedTeams }),
            success: function (response) {
                alert(response.message);

                // Update the managed and followed teams lists on the dashboard
                const managedTeamsList = $('#managedTeamsList');
                managedTeamsList.empty();
                response.managed_teams.forEach(team => {
                    managedTeamsList.append(`<li>${team.team_name} (Stat Group: ${team.stat_group})</li>`);
                });

                const followedTeamsList = $('#followedTeamsList');
                followedTeamsList.empty();
                response.followed_teams.forEach(team => {
                    followedTeamsList.append(`<li>${team.team_name} (Stat Group: ${team.stat_group})</li>`);
                });

                // Update the Remove Teams Modal
                updateRemoveTeamsModal(response.managed_teams, response.followed_teams);

                // Close the modal
                $('#removeTeamsModal').modal('hide');
            },
            error: function (xhr) {
                alert('An error occurred: ' + xhr.responseText);
            }
        });
    });
});

