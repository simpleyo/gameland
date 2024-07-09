#pragma once

#include "core/defs.h"
#include "main/cmain.h"
#include "engine/iview.h"
#include "engine/simple/view_renderer.h"
#include "engine/simple/context.h"

class EngineContext : public engine::simple::Context
{
public:
    static EngineContext* get_singleton() { return _singleton; }

    EngineContext();
    virtual ~EngineContext();

    void setup() override;

    uint UPS() const override { return Main::UPS(); }

    void on_prepare_to_be_begined(IDR room_id, double prev_delta) override;
    void on_prepare_ended(IDR room_id, double prev_delta) override;
    
    IDR get_current_processing_room() const override { return _current_processing_room; }

    /////////////////////////////////////////
    // View
    //
    IDR  create_view(IDR gmap_id, IDR room_id, IDR play_session_id/*, const engine::ViewCreationParameters& vcp*/) override;
    void terminate_view(IDR gmap_id, IDR view_id) override;

    void view_send(const engine::simple::View& view, const engine::simple::ViewRenderer::Output& output) override;
    void view_recv(engine::simple::View& view) override;
    
    //void on_view_game_over(IDR play_session_id, const engine::ViewGameOver& game_over_data) override;
    //
    /////////////////////////////////////////

    /////////////////////////////////////////
    // GMap
    //
    IDR  create_gmap(IDR room_id, const std::string& map_name) override;
    void terminate_gmap(IDR gmap_id) override;
    const json& gmap_get_config(IDR gmap_id) override;

    void on_gmap_constructed            (IDR room_id) override;
    void on_gmap_waiting_for_players    (IDR room_id) override; 
    void on_gmap_play_started           (IDR room_id) override; 
    void on_gmap_waiting_for_play_finish(IDR room_id) override; 
    void on_gmap_play_to_be_finished    (IDR room_id) override;
    void on_gmap_play_finished          (IDR room_id) override;
    void on_gmap_to_be_deleted          (IDR room_id) override;
    //
    /////////////////////////////////////////

    /////////////////////////////////////////
    // Race
    //
    void on_race_player_event(IDR room_id, const engine::RacePlayerEvent& rpe) override;
    void on_race_finished  (IDR room_id) override;
    void on_race_terminated(IDR room_id) override;
    //
    /////////////////////////////////////////


private:
    static EngineContext* _singleton;

    IDR _current_processing_room;
};
