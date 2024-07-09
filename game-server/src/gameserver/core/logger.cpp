#include <iostream>
#include <fstream>
#include <string>
#include <vector>
#include <mutex>
#include <thread>

#include "config/config.h"
#include "core/circularbuffer.h"
#include "core/types.h"
#include "core/logger.h"

//#define THREAD_SAFE_LOGGER

static const uint LOGGER_CIRCULAR_BUFFER_MAX_SIZE = 100;

class Logger 
{
public:
    Logger() : _circular_buffer(LOGGER_CIRCULAR_BUFFER_MAX_SIZE), _console_output_enabled(true), _circular_file_output_enabled(true)
    {
        _log_file_name = "log-gameserver-" + _gen_random(8) + ".log";
    }

    ~Logger() 
    {
        if (_circular_file_output_enabled)
        {
            _write_circular_buffer_to_file();
        }
    }

    void log(const std::string& msg) 
    {
#ifdef THREAD_SAFE_LOGGER
        std::lock_guard<std::mutex> lock(_log_mutex);
#endif
        if (_console_output_enabled)
            std::cout << msg;

        if (_circular_file_output_enabled)
        {
            if (!_circular_buffer.empty())
                if (_circular_buffer.full())
                    _circular_buffer.pop_front();

            _circular_buffer.push_back(msg);
        }
    }

    void configure() 
    {
        _circular_buffer.set_capacity(GET_CONFIG_VALUE(uint, "LOGGER_CIRCULAR_BUFFER_CAPACITY")); 
                
        if (EXISTS_CONFIG_PATH("LOGGER_CONSOLE_OUTPUT"))
            _console_output_enabled = GET_CONFIG_VALUE(bool, "LOGGER_CONSOLE_OUTPUT"); 

        if (EXISTS_CONFIG_PATH("LOGGER_CIRCULAR_FILE_OUTPUT")) 
            _circular_file_output_enabled = GET_CONFIG_VALUE(bool, "LOGGER_CIRCULAR_FILE_OUTPUT"); 
    }

    void disable_console_output() { _console_output_enabled = false; }

private:
    void _write_circular_buffer_to_file();
    std::string _gen_random(int len);

private:
    CircularBuffer<std::string> _circular_buffer;

    bool _console_output_enabled;
    bool _circular_file_output_enabled;
    std::string _log_file_name;

#ifdef THREAD_SAFE_LOGGER
    std::mutex _log_mutex;
#endif
};

std::string Logger::_gen_random(int len) {
    static const char alphanum[] =
        "0123456789"
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        "abcdefghijklmnopqrstuvwxyz";
    std::string tmp_s;
    tmp_s.reserve(len);

    for (int i = 0; i < len; ++i) {
        tmp_s += alphanum[rand() % (sizeof(alphanum) - 1)];
    }

    return tmp_s;
}

void Logger::_write_circular_buffer_to_file()
{
    std::ofstream o;
    o.open(_log_file_name);
    const uint ei = _circular_buffer.size();
    for (uint i=0; i<ei; ++i)
    {
        const auto& msg = _circular_buffer[i];
        //o << "[" << i << "]: ";
        o << msg;
    }    

    std::time_t t = std::time(nullptr);
    char mbstr[100];
    if (std::strftime(mbstr, sizeof(mbstr), "%A %c", std::localtime(&t))) {
        o << mbstr << '\n';
    }

    o.close();
}



///////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////



static Logger* logger = NULL;

void logger_init()
{
    if (logger == NULL)
    {
        logger = new Logger();
    }
}

void logger_term()
{
    if (logger != NULL)
    {
        delete logger;
        logger = NULL;
    }
}

void logger_configure()
{
    if (logger != NULL)
    {
        logger->configure();
    }
}

void logger_log(const std::string& msg)
{
    if (logger != NULL)
    {
        logger->log(msg);
    }
}

void logger_disable_console_output()
{
    if (logger != NULL)
    {
        logger->disable_console_output();
    }
}


