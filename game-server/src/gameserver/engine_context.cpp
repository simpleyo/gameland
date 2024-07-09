#pragma once

#include "core/defs.h"
#include "core/json/include/json.hpp"
#include "core/utils.h"
#include "core/timers.h"
#include "engine/irace.h"
#include "engine/simple/view.h"
#include "engine/simple/ranking.h"
#include "engine/simple/radar.h"
#include "engine/simple/gmap.h"
#include "engine/simple/race.h"
#include "engine/simple/time.h"
#include "engine/simple/player_manager.h"
#include "engine/simple/tank_manager.h"
#include "engine/simple/view_manager.h"
#include "engine/simple/gmap_config.h"
#include "engine/simple/gmap_manager.h"
#include "engine_context.h"
#include "modules/event/event_manager.h"
#include "modules/ws/server.h"
#include "modules/user/user_manager.h"
#include "modules/main_server_client/resource_manager.h"
#include "modules/game_context/game_context.h"
#include "modules/game_context/room.h"
#include "modules/game_context/game_session.h"
#include "modules/game_context/play_session.h"
#include "packet_builder.h"

using namespace engine;
using namespace engine::simple;

EngineContext* EngineContext::_singleton = NULL;

EngineContext::EngineContext()
{
    RTCHECK(!_singleton);
    _singleton = this;
}

EngineContext::~EngineContext()
{
    RTCHECK(_singleton);
	_singleton = NULL;
}

void EngineContext::setup()
{
    // Aqui se puede inicializar el contexto.
}

void EngineContext::on_prepare_to_be_begined(IDR room_id, double prev_delta)
{
    _current_processing_room = room_id;

    //GET_SINGLETON(GameContext, gc);
    //gc->get_room(room_id).on_prepare_to_be_begined();

#if 1
    static uint64 tc_last_ticks = 0;
    const uint64 tc_now_ticks = get_ticks_usec();
    //TRACE("Ticks diff: " << now_ticks - last_ticks);
    if ((tc_now_ticks - tc_last_ticks) > 5000) // Se llama a poll cada 5000 microsegundos como maximo.
    {
        tc_last_ticks = tc_now_ticks;

        const uint64 tc_poll_begin = get_ticks_usec();
        GET_SINGLETON(ws::Server, wss); // Websockets server.
        if (wss->is_listening())
        {
            wss->poll();
        }
        const uint64 tc_poll_end = get_ticks_usec();
        //TRACE("Poll[" << room_id << "]: " << tc_poll_end - tc_poll_begin);

        const uint64 tc_exec_begin = get_ticks_usec();
        //SINGLETON(EventManager)->execute_room_events(_current_processing_room);
        SINGLETON(EventManager)->execute_all_events();
        const uint64 tc_exec_end = get_ticks_usec();
        //TRACE("Exec[" << room_id << "]: " << tc_exec_end - tc_exec_begin);
    }
#else

    GET_SINGLETON(ws::Server, wss); // Websockets server.
    if (wss->is_listening())
    {
        wss->poll();
    }

    SINGLETON(EventManager)->execute_all_events();

#endif
}

void EngineContext::on_prepare_ended(IDR room_id, double prev_delta)
{
    _current_processing_room.invalidate();

    //Ranking* ranking = Ranking::get_singleton(); RTCHECK(ranking);
    //ranking->update_ranking();

    //Radar* radar = Radar::get_singleton(); RTCHECK(radar);
    //radar->update_radar(prev_delta);

    //// Aqui se deberian construir los paquetes RANKING y RADAR
    //// ATENCION: Hay un problema con esto porque cada cliente puede tener una version y un transmision mode
    //// personalizado. Por lo tanto no se puede enviar el mismo paquete para todos ellos.
    //// La solucion a esto es que los clientes solo puedan funcionar con la version y el transmision mode
    //// que les indique el servidor.
    //// Otra "solucion" (lo que esta ahora) es forzar que los paquetes RANKING y RADAR se envien con la version y el modo de transmision
    //// elegido por el servidor siendo estas elecciones conocidas previamente por los clientes (antes de su compilacion).
    //// En realidad esta "solucion" tiene el mismo efecto que la solucion de los clientes solo puedan funcionar 
    //// con la version y el transmision mode que les indique el servidor, pero es mas sencilla de implementar ya
    //// que todo lo que hay implementado presupone que cada cliente puede elegir ambos valores (y habria que cambiarlo todo).
    //
    //PacketBuilder* pkb = PacketBuilder::get_singleton(); RTCHECK(pkb);
    //pkb->build_RANKING(1, TransmissionMode::Text);
    //PacketBuilder::Packet pk = pkb->get_packet();
    //Ranking* ranking = Ranking::get_singleton(); RTCHECK(ranking);
    //ranking->set_ranking_packet(BytesView(pk.data, pk.size));
}

static bool _build_view_creation_parameters(GMap& gmap, IDR play_session_id, engine::ViewCreationParameters& vcp);

IDR EngineContext::create_view(IDR gmap_id, IDR room_id, IDR play_session_id/*, const engine::ViewCreationParameters& vcp*/)
{
    GET_SINGLETON(GMapManager, mm);
    IDR view_id;
    if (mm->contains_gmap(gmap_id))
    {
        GMap& gmap = mm->get_gmap(gmap_id);
        
        engine::ViewCreationParameters vcp;
        
        RTCHECK(play_session_id.is_valid());
        vcp.play_session_id = play_session_id;

        if (_build_view_creation_parameters(gmap, play_session_id, vcp))
        {
            RTCHECK(room_id.is_valid());
            vcp.room_id = room_id;

            ViewManager* vm = gmap.component<ViewManager>();
            view_id = vm->create_view(vcp);
        }
    }
    return view_id;
}

void EngineContext::terminate_view(IDR gmap_id, IDR view_id)
{
    GET_SINGLETON(GMapManager, mm);
    if (mm->contains_gmap(gmap_id))
    {
        ViewManager* vm = mm->get_gmap(gmap_id).component<ViewManager>();
        vm->get_view(view_id).terminate();
        //vm->delete_view(view_id);
    }
}

//void EngineContext::view_abort(IDR gmap_id, IDR view_id)
//{
//    GET_SINGLETON(GMapManager, mm);
//    if (mm->contains_gmap(gmap_id))
//    {
//        ViewManager* vm = mm->get_gmap(gmap_id).component<ViewManager>();
//        vm->get_view(view_id).on_abort_view_forced();
//    }
//}

void EngineContext::view_send(const View& view, const ViewRenderer::Output& output)
{
#ifndef _DEBUG
    // Para comprobar la diferencia de tiempo real que hay entre los mensajes enviados.
    //{
    //    const uint MAX_ROOMS = 64;
    //    const uint MAX_VIEWS = 256;
    //    const IDR room_id = view.get_room_id();
    //    const IDR view_id = view.get_id();
    //    if ((room_id < MAX_ROOMS) && (view_id < MAX_VIEWS))
    //    {
    //        //if ((room_id == 0) && (view.get_id()==0))
    //        {
    //            static uint64_t counter[MAX_ROOMS][MAX_VIEWS];
    //            static uint64_t last_ticks[MAX_ROOMS][MAX_VIEWS];
    //            const uint64_t ticks = get_ticks_usec();
    //            const double diff = (double(ticks - last_ticks[room_id][view_id]) / 1000000);
    //            //if (diff < 0.03)
    //            {
    //                TRACE("----> WARNING: Room[" << room_id << "] View [" << view.get_id() << "] Sending VIEW_RESULTS[" << counter[room_id][view_id] << "]... Diff: " << std::fixed << std::setprecision(3) << diff << " seg.");
    //            }
    //            ++counter[room_id][view.get_id()];
    //            last_ticks[room_id][view_id] = ticks;
    //        }        
    //    }
    //}
#endif

    GET_SINGLETON(GameContext, gc);
    Room& room = gc->get_room(view.get_room_id());

    const IDR play_session_id = view.get_play_session_id();
    if (room.contains_play_session(play_session_id))
    {
        PlaySession& session = room.get_play_session(play_session_id);
        if (session.is_running())
        {
            GET_SINGLETON(UserManager, ncm);
            const IDR user_id = session.get_user_id();
            if (ncm->contains_user(user_id))
            {
                User& user = ncm->get_user(user_id);

                //TRACE("VIEW_RESULTS: " << client_time);

                // send view results
                PKB_SEND_PACKET(VIEW_RESULTS, view.get_gmap(), view.get_id(), session, output);

                Time* engine_time = Time::get_singleton();
                RTCHECK(engine_time);

#if 0 // Ahora el RADAR se envia en VIEW_RESULTS.
                // send radar
                {
                    // ATENCION: Esta funcion, <view_send>, se ejecutan tantas veces por time step como clientes haya,
                    // asi que el paquete RADAR es enviado varias veces en cada step.

                    // FIXME: El paquete RADAR se deberia construir en Context::on_render_begined() y se deberia enviar aqui.

                    Radar* radar = view.get_gmap()->component<Radar>();
                    RTCHECK(radar != NULL);

                    if (radar->get_radar_list_changed())
                    {
                        //TRACE("----------> CHANGED RADAR");
                        PKB_SEND_PACKET(RADAR, view.get_gmap()); // FIXME
                    }
                }
#endif

#if 0 // Ahora el GMAP se envia en VIEW_RESULTS.
                // send gmap
                {
                    if (view.get_gmap()->get_changes() != 0)
                    {
                        if (view.get_gmap()->get_play_status() != GMapPlayStatus::PlayToBeFinished)
                            PKB_SEND_PACKET(GMAP, view.get_gmap());
                    }
                }
#endif
            }
            else
            {
                // UserManager no contiene a user_id.
            }
        }
        else
        {
            // Play session no esta running.
        }
    }
    else
    {
        // Room no contiene a play_session_id.
    }
}

void EngineContext::view_recv(View& view)
{
    GET_SINGLETON(GameContext, gc);
    Room& room = gc->get_room(view.get_room_id());

    IDR play_session_id = view.get_play_session_id();
    if (room.contains_play_session(play_session_id))
    {
        PlaySession& session = room.get_play_session(play_session_id);
        
        if (session.is_running())
        {
            // La sesion esta en ejecucion.
            view.input(session.on_input_state_to_be_readed_by_view());            
        }
        else 
        {
            if (session.is_finished())
            {
                // La sesion esta finalizada.
            }
            else
            {
                // La sesion esta creada pero todavia no ha empezado.
            }
        }
    }
}

//void EngineContext::on_view_game_over(IDR play_session_id, const ViewGameOver& game_over_data)
//{
//    GET_SINGLETON(GameContext, gc);
//    Room& room = gc->get_room();
//    if (room.contains_play_session(play_session_id))
//    {
//        PlaySession& ps = room.get_play_session(play_session_id);
//        ps.on_game_over(game_over_data);
//    }
//}

//void EngineContext::on_view_player_avatar_deleted(IDR play_session_id)
//{
//    GET_SINGLETON(GameContext, gc);
//    Room& room = gc->get_room();
//    RTCHECK(room.contains_play_session(play_session_id));
//    PlaySession& ps = room.get_play_session(play_session_id);
//    ps.on_game_over();
//}

//void EngineContext::on_view_finalized(IDR play_session_id)
//{
//    GET_SINGLETON(GameContext, gc);
//    Room& room = gc->get_room();
//    RTCHECK(room.contains_play_session(play_session_id));
//    PlaySession& ps = room.get_play_session(play_session_id);
//    ps.on_game_finished();
//}
//
//void EngineContext::on_view_aborted(IDR play_session_id)
//{
//    GET_SINGLETON(GameContext, gc);
//    Room& room = gc->get_room();
//    RTCHECK(room.contains_play_session(play_session_id));
//    PlaySession& ps = room.get_play_session(play_session_id);
//    ps.on_game_aborted();
//}

#if 0
void EngineContext::on_avatar_to_be_deleted(IDR play_session_id)
{
    GET_SINGLETON(GameContext, gc);
#if 0
    PlaySession& session = gc->get_play_session(play_session_id);
    session.on_game_over();
#endif
}

void EngineContext::on_view_to_be_deleted(IDR play_session_id)
{
    GET_SINGLETON(GameContext, gc);
    if (gc->contains_play_session(play_session_id))
    {
        PlaySession& session = gc->get_play_session(play_session_id);
        session.on_view_to_be_deleted();
    }
}
#endif

IDR EngineContext::create_gmap(IDR room_id, const std::string& map_name)
{
    // Crea el GMap en el engine a partir de los datos de configuracion.
    // El GMap es necesario para crear las PlaySession's ya que el GMap es
    // el dueño de la View's.
    
    GET_SINGLETON(ResourceManager, rm);
    GET_SINGLETON(GMapManager, mm);
    GMapCreationParameters cp;
    cp.room_id = room_id;
    cp.gmap_config = GameContext::get_game_resource("maps/" + map_name + "/map.cfg");    
    //cp.gmap_config = GameContext::get_game_resourceLOAD_GAME_RESOURCE("maps/" + map_name + "/map.cfg");    

    const IDR gmap_id = mm->create_gmap(cp);
    RTCHECK(gmap_id.is_valid());

    return gmap_id;
}

void EngineContext::terminate_gmap(IDR gmap_id)
{
    GET_SINGLETON(GMapManager, mm);
    mm->get_gmap(gmap_id).terminate();
    //mm->delete_gmap(gmap_id);
}

const json& EngineContext::gmap_get_config(IDR gmap_id)
{
    GET_SINGLETON(GMapManager, mm);
    RTCHECK(mm->contains_gmap(gmap_id));
    const GMap& gmap = mm->get_gmap(gmap_id);
    const json* js = gmap.config().get_config_json("");
    RTCHECK(js != NULL);
    return *js;
}

void EngineContext::on_gmap_constructed(IDR room_id)
{
    GET_SINGLETON(GameContext, gc);
    GameSession* gs = gc->get_room(room_id).get_game_session();
    if (gs)
        gs->on_gmap_constructed();
}

void EngineContext::on_gmap_waiting_for_players(IDR room_id)
{
    GET_SINGLETON(GameContext, gc);
    GameSession* gs = gc->get_room(room_id).get_game_session();
    if (gs)
        gs->on_gmap_waiting_for_players();
}

void EngineContext::on_gmap_play_started(IDR room_id)
{
    GET_SINGLETON(GameContext, gc);
    GameSession* gs = gc->get_room(room_id).get_game_session();
    if (gs)
        gs->on_gmap_play_started();
}

void EngineContext::on_gmap_waiting_for_play_finish(IDR room_id)
{
    GET_SINGLETON(GameContext, gc);
    GameSession* gs = gc->get_room(room_id).get_game_session();
    if (gs)
        gs->on_gmap_waiting_for_play_finish();
}

void EngineContext::on_gmap_play_to_be_finished(IDR room_id)
{
    GET_SINGLETON(GameContext, gc);
    GameSession* gs = gc->get_room(room_id).get_game_session();
    if (gs)
        gs->on_gmap_play_to_be_finished();
}

void EngineContext::on_gmap_play_finished(IDR room_id)
{
    GET_SINGLETON(GameContext, gc);
    GameSession* gs = gc->get_room(room_id).get_game_session();
    if (gs)
        gs->on_gmap_play_finished();
}

void EngineContext::on_gmap_to_be_deleted(IDR room_id)
{
    GET_SINGLETON(GameContext, gc);
    GameSession* gs = gc->get_room(room_id).get_game_session();
    if (gs)
        gs->on_gmap_to_be_deleted();
}

void EngineContext::on_race_player_event(IDR room_id, const engine::RacePlayerEvent& rpe)
{
    GET_SINGLETON(GameContext, gc);
    GameSession* gs = gc->get_room(room_id).get_game_session();
    if (gs)
        gs->on_race_player_event(rpe);
}

void EngineContext::on_race_finished(IDR room_id)
{
    GET_SINGLETON(GameContext, gc);
    GameSession* gs = gc->get_room(room_id).get_game_session();
    if (gs)
        gs->on_race_finished();
}

void EngineContext::on_race_terminated(IDR room_id)
{
    GET_SINGLETON(GameContext, gc);
    GameSession* gs = gc->get_room(room_id).get_game_session();
    if (gs)
        gs->on_race_terminated();
}

bool _build_player_creation_parameters(GMap& gmap, PlaySession& ps, engine::PlayerCreationParameters& pcp);

bool _build_view_creation_parameters(GMap& gmap, IDR play_session_id, engine::ViewCreationParameters& vcp)
{
    GET_SINGLETON(GameContext, gc);
    Room& room = gc->get_room(gmap.get_room_id());
    if (room.contains_play_session(play_session_id))
    {
        PlaySession& ps = room.get_play_session(play_session_id);        
        if (_build_player_creation_parameters(gmap, ps, vcp.player_cp))
        {
            vcp.tracker_cp._view = NULL;
            vcp.tracker_cp.radius = Vector2(gmap.config().TRACKER_DEFAULT_WIDTH / 2.f, 
                                            gmap.config().TRACKER_DEFAULT_HEIGHT / 2.f);   // radius of the bounding box of the tracker
                        
            vcp.render_disabled = false/*vcp.player_cp.is_bot*/; // FIXME: Usado en debug. Dejo el FIXME para poder localizarlo facilmente.

            return true;
        }
    }

    return false;
}

bool _build_player_creation_parameters(GMap& gmap, PlaySession& ps, engine::PlayerCreationParameters& pcp)
{
    static const uint DEFAULT_TANK_MASS  = 1000;
    static const uint DEFAULT_TANK_SPEED = 260;    // Pixeles por segundo.

    TankManager* tm = gmap.component<TankManager>();
    if (tm->full()) return false;

    GET_SINGLETON(UserManager, ncm);
    const User& user = ncm->get_user(ps.get_user_id());

    const float vel = DEFAULT_TANK_SPEED;

    const uint max_world_coords = (1 << gmap.config().WORLD_COORD_BITS); 

    const AccountSession& as = user.get_account_session();

    Vector2 spawn_position;
    float spawn_orientation; 
    bool valid_spawn_data = false;

    TankCreationParameters cp;
    
    // ATENCION: Esto parece que da problemas porque ha pasado que un jugador ha terminado la carrera de 2 vueltas
    // cuando todavia quedaba una por terminar.
    // Si la Race ha comenzado entonces se intenta obtener la ultima posicion y orientacion conocida del player con menor race progress.
    //{
    //    Race* race = gmap.component<Race>();
    //    if (race->get_max_laps() > 1) // Solo se aplica cuando el numero maximo de vueltas del mapa es mayor que 1.
    //    {
    //        if (race->get_status() == RaceStatus::Started)
    //        {
    //            const IDR prp = race->get_player_with_less_race_progress();
    //            if (prp.is_valid())
    //            {
    //                PlayerManager* pm = gmap.component<PlayerManager>();
    //                if (pm->contains_player(prp))
    //                {
    //                    const Player& player = pm->get_player(prp);
    //                    const Avatar* avatar = player.get_avatar();
    //                    if (avatar && (avatar->get_avatar_type() == AvatarType::Tank))
    //                    {
    //                        const Tank* tank = (Tank*)avatar;
    //                        if (tank->get_race_data().last_visited_road_and_terrain_cell_id)
    //                        {
    //                            cp.template_player_id = prp;
    //                            valid_spawn_data = true;
    //                        }
    //                    }
    //                }
    //            }
    //        }
    //    }
    //}

    if (!valid_spawn_data)
    {
        gmap.acquire_spawn_position(spawn_position, spawn_orientation);

        cp.position = spawn_position; //Vector2(max_world_coords-500.f/*max_world_coords/2.f*/, max_world_coords/2.f);
        cp.orientation = spawn_orientation;
        valid_spawn_data = true;
    }

    cp.velocity = Vector2(vel /** rand_vx*/, 0 /** rand_vy*/); 

    pcp._view = NULL;
    pcp.player_type = PlayerType::Avatar;
    pcp.avatar.avatar_type = AvatarType::Tank; 
    pcp.avatar.avatar_id = tm->create_tank(cp);

    pcp.is_bot = user.bot();

    pcp.user_data.name.set(as.display_name.c_str());
    
    RTCHECK(as.skin_index < (uint)as.skin_ids.size());
    pcp.user_data.skin_id = as.skin_ids[as.skin_index]; // as.skin_id;
    
    RTCHECK(as.flag_index < (int)as.flag_ids.size());
    if (as.flag_index >= 0)
        pcp.user_data.flag_id = as.flag_ids[as.flag_index];
    else
        pcp.user_data.flag_id.invalidate();

    pcp.user_data.color_id = as.color_id;

    return true;
}
