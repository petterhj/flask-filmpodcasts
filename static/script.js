// FILMPODCASTS
var FILMPODCASTS = FILMPODCASTS || {
    // Options
    options: {
        name: 'FILMPODCASTS'
    },

    // Templates
    templates: {
        episode: undefined
    },

    // Init
    init: function() {
        console.log('Initializing...');

        // Compile templates
        FILMPODCASTS.templates.episode = Handlebars.compile($('#episode_template').html());

        // Status
        $.getJSON('/json/status/', function(data) {
            // Stats
            $('#stats > .podcasts').text('Podcasts: {0}'.format(data.database.podcasts));
            $('#stats > .episodes').text('Episodes: {0}'.format(data.database.episodes));
            if (data.scheduler.ended_at) {
                var ended_at = moment(data.scheduler.ended_at);
                var scheduled_for = moment(data.scheduler.scheduled_for);
                var next_sync = scheduled_for.fromNow();
                
                console.log('NOW: {0}'.format(moment().format('YYYY-MM-DD - HH:mm')));
                console.log('LST: {0}'.format(ended_at.format('YYYY-MM-DD - HH:mm')));
                console.log('NXT: {0}, {1}'.format(scheduled_for.format('YYYY-MM-DD - HH:mm'), next_sync));
                console.log();

                $('#stats > .synced').show().text('Last sync {0} [{1}], next scheduled {2}'.format(
                    ended_at.format('YYYY-MM-DD - HH:mm'),
                    data.scheduler.status,
                    next_sync
                )).attr('class', 'synced ' + data.scheduler.status);
            } else {
                $('#stats > .synced').hide();
            }

            // Results
            $.each(data.scheduler.result, function(pid, result) {
                console.log('PID: {0}, SYNCED={1}, IGNORED={2}'.format(pid, result.synced, result.ignored));
                
                var podcast = $('.podcast[data-podcast-id="{0}"]'.format(pid));

                if (podcast.length > 0) {
                    if (result.synced > 0) {
                        podcast.find('span.title').append(
                            $('<span>', {class: 'synced'}).text('+{0}'.format(result.synced))
                        );
                    }
                    if ((result.synced == 0) && (result.ignored == 0)) {
                        podcast.find('span.title').append(
                            $('<span>', {class: 'warning'}).append($('<i class="zmdi zmdi-alert-circle-o"></i>'))
                        );
                    }
                }
            });
        });

        // Search
        $('input[name="query"]').focus().on('keypress', function (e) {
            if(e.which === 13) {
                FILMPODCASTS.search($('input').val());
            }
        });

        $('button[name="search"]').on('click', function() {
            FILMPODCASTS.search($('input').val());
        });

        $('button[name="clear"]').on('click', function() {
            $('input').val('');
            
            // Show last episodes
            $.getJSON('/json/podcasts/episodes/', function(data) {
                $('.container .card').fadeOut(400, function() {
                    $(this).remove();
                });

                $.each(data, function(i, episode) {
                    FILMPODCASTS.addEpisode(episode);
                });
            });
        }).trigger('click');
    },

    addEpisode: function(episode, highlight) {
        // Render episode card
        episode.pubdate = moment(episode.pubdate).format('DD-MM-YYYY');

        var card = $(FILMPODCASTS.templates.episode(episode));

        if (highlight) {
            card.mark(highlight, {
                separateWordSearch: false
            });
        }

        card.appendTo($('.container'));
    },

    // Search
    search: function(query) {
        if (!query || query === '') {
            return;
        }

        query = $.trim(query);

        $('input').val(query);

        console.log('Searching "{0}"'.format(query));

        $('.container .card').fadeOut(400, function() {
            $(this).remove();
        });

        $.getJSON('/json/search/?title={0}'.format(query), function(data) {
            $.each(data.results, function(i, result) {
                FILMPODCASTS.addEpisode(result, query);
            });
        });
    }
};

$(document).ready(FILMPODCASTS.init);
