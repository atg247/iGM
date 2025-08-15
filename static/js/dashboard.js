$(document).ready(function () {

    (function() {
        const $loading = $('#loadingIndicator');
      
        function showLoading()  { $loading.addClass('is-visible'); }
        function hideLoading()  { $loading.removeClass('is-visible'); }
      
        // Näytä kun ensimmäinen AJAX starttaa, piilota kun KAIKKI ovat valmiit
        $(document).ajaxStart(showLoading);
        $(document).ajaxStop(hideLoading);
      
        // (valinnainen) jos haluat varmuudeksi piilottaa virheissäkin:
        $(document).ajaxError(() => { /* ei piiloteta tässä, ajaxStop hoitaa kun kaikki päättyy */ });
      
        // Jos overlaylle on joskus jäänyt is-visible (esim. edeltävältä sivulta cached DOM)
        $(hideLoading);
      })();

    

    
    // Fetch levels based on season selection
    $('#season').change(function () {
        const season = $(this).val();
        if (season) {
            $.get(`api/gamefetcher/get_levels/${season}`, function (data) {
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
            $.get(`api/gamefetcher/get_statgroups/${season}/${levelId}/0`, function (data) {
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
            $.get(`api/gamefetcher/get_teams/${season}/${statGroupId}`, function (data) {
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
    
    
// Function to load the latest teams data from the server
function loadTeams() {
    return $.ajax({
        url: 'dashboard/get_ManagedFollowed', // Assumes a backend endpoint to fetch the latest teams data
        method: 'GET',
        success: function (response) {
            console.log('Hallinnoidut joukkueet:', response);
            // Update the managed teams list
            const managedTeamsList = $('#managedTeamsList');
            managedTeamsList.empty();
            response.managed_teams.forEach(team => {
                managedTeamsList.append(`<li data-team-id="${team.team_id}">${team.team_name} (${team.stat_group})</li>`);
            });

            // Update the followed teams list
            const followedTeamsList = $('#followedTeamsList');
            followedTeamsList.empty();
            response.followed_teams.forEach(team => {
                followedTeamsList.append(`<li data-team-id="${team.team_id}">${team.team_name} (${team.stat_group})</li>`);
            });

            // Store the jopox managed team in a variable
            const jopoxManagedTeam = response.jopox_managed_team;
            const jopox_url = response.jopox_url;
            const jopox_username = response.jopox_username;
            
            // Update the HTML element with the jopox managed team
            // Update the HTML element with the jopox managed team
            if (jopoxManagedTeam) {
                $('#jopoxManagedTeam').text(jopoxManagedTeam);
            } else {
                $('#jopoxManagedTeam').text('Et hallinnoi tällä hetkellä mitään Jopox-joukkuetta.');
            }

    // Update modal with the latest data
    updateRemoveTeamsModal(response.managed_teams, response.followed_teams);
        },
        error: function (xhr) {
            console.error("Error fetching teams:", xhr.responseText);
        }
    });
}

// Function to update Remove Teams Modal content
function updateRemoveTeamsModal(managedTeams, followedTeams) {
    const managedTeamsModalList = $('#removeManagedList');
    const followedTeamsModalList = $('#removeFollowedList');

    managedTeamsModalList.empty();
    followedTeamsModalList.empty();

    managedTeams.forEach(team => {
        managedTeamsModalList.append(`
            <li>
                <input type="checkbox" name="teams" value="${team.team_id}" data-relationship="manage">
                ${team.team_name} (Stat Group: ${team.stat_group})
            </li>
        `);
    });

    followedTeams.forEach(team => {
        followedTeamsModalList.append(`
            <li>
                <input type="checkbox" name="teams" value="${team.team_id}" data-relationship="follow">
                ${team.team_name} (Stat Group: ${team.stat_group})
            </li>
        `);
    });
}

// Trigger change to pre-populate levels when the page loads
$('#season').trigger('change');

// Load latest teams initially
loadTeams();

// Handle add/update teams submission
let selectedAction = null; // Tallennetaan painikkeen arvo

// Tallenna painikkeen arvo klikkaustapahtuman yhteydessä
$('#dashboardForm button[type="submit"]').on('click', function () {
    selectedAction = $(this).val(); // Aseta valittu action-arvo
});

    

// Lomakkeen lähetys JSON-muotoisena
$('#dashboardForm').on('submit', function (e) {
    e.preventDefault(); // Estä lomakkeen oletuslähetys

    if (!selectedAction) {
        alert("Action not specified.");
        return;
    }

    // Valitse joukkueet
    const selectedTeams = $('#teams option:selected').map(function () {
        return {
            TeamID: $(this).val(),
            TeamAbbrv: $(this).data('abbrv'),
            team_association: $(this).data('association'),
            team_name: $(this).data('name'),
            stat_group: $(this).data('statgroup'),
            season: $('#season').val(),
            level_id: $('#levels').val(),
            statgroup: $('#statgroups').val(),
        };
    }).get();

    // Rakennetaan JSON-data
    const data = {
        action: selectedAction, // Käytä tallennettua action-arvoa
        teams: selectedTeams,
    };

    // Lähetä JSON-pyyntö
    $.ajax({
        url: '/dashboard/update_teams',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify(data), // Muunna JSONiksi
        success: function (response) {
            console.log('Success:', response);
            loadTeams(); // Päivitä joukkueiden listat
        },
        error: function (xhr) {
            console.error('Error:', xhr.responseText);
            alert(`An error occurred: ${xhr.responseText}`);
        },
    });
});

$(document).ready(function () {

    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('activate_jopox') === 'True') {
        $('#jopoxAuthModal').modal('show');
    }

    // Aktivoi Jopox-yhteys -painike
    $('#activateJopox').click(function () {
        $('#jopoxAuthModal').modal('show');  // Näytä modaalinen ikkuna
    });

   
    $('#clearJopox').click(function () {

        // Kysy käyttäjältä vahvistus
        if (confirm('Haluatko varmasti tyhjentää Jopox-tietosi?')) {

        // kutsu backendin clear_jopox_credentials -funktiota
        $.get('/dashboard/clear_jopox_credentials', function (response) {
            });
        }

        // päivitä painike jopoxin aktivointiin
        $('#activateJopox').text('Aktivoi Jopox-yhteys');
        // Päivitä sivu
        location.reload();


    });


    // Tietojen tallentaminen Jopoxiin
    $('#jopoxAuthForm').submit(function (e) {
        e.preventDefault();
        
        const jopoxLoginUrl = 'https://login.jopox.fi';
        const jopoxUsername = $('#jopoxUsername').val();
        const jopoxPassword = $('#jopoxPassword').val();

        // Lähetä tiedot backendille
        $.ajax({
            url: '/dashboard/save_jopox_credentials',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({
                jopoxLoginUrl: jopoxLoginUrl,
                username: jopoxUsername,
                password: jopoxPassword
            }),
            // lisää latausindikaattori
            beforeSend: function () {
                $('#loadingIndicator').show();
            },
            complete: function () {
                $('#loadingIndicator').hide();
            },
            
            success: function (response) {
                console.log('Jopox-tiedot tallennettu:', response);
                $('#jopoxAuthModal').modal('hide');  // Sulje modaalinen ikkuna
                loadTeams();  // Päivitä tiimit
                // lataa sivu uudelleen
                location.reload();

            },
            error: function (xhr) {
                alert('Virhe tallentaessa tietoja: ' + xhr.responseText);
            }
        });
    });
});

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

            loadTeams(); // Refresh lists and modal with latest data after removal

            // Close the modal
            $('#removeTeamsModal').modal('hide');
        },
        error: function (xhr) {
            alert('An error occurred: ' + xhr.responseText);
        }
    });
});

// Re-fetch and update modal content each time it opens to ensure fresh data
$('#removeTeamsModal').on('show.bs.modal', function () {
    loadTeams(); // Fetch the latest data to populate the modal
});
});

