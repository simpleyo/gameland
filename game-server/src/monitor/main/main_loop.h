#pragma once

#include <vector>

class Timers;

class MainLoop
{
public:
    static MainLoop* get_singleton() { return _singleton; }

    MainLoop();
    virtual ~MainLoop();

    void init();

    // Si retorna true entonces el loop termina.
    bool iteration(double p_fixed_delta);

    void idle(double p_delta);

    void finish();

    void quit();

private:
    static MainLoop* _singleton;

    std::unique_ptr<Timers> _timers; // Se utilizan para timeout superiores al p_fixed_delta de iteration(). Si son inferiores entonces llamar en idle() directamente.
};

