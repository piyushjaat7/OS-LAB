
#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>
#include <time.h>
#include <unistd.h>

static pthread_mutex_t resource1;
static pthread_mutex_t resource2;

static struct timespec
timeout_after_one_second(void)
{
    struct timespec limit;

    clock_gettime(
        CLOCK_REALTIME,
        &limit
    );

    limit.tv_sec += 1;

    return limit;
}

static void *thread1(void *argument)
{
    (void)argument;

    pthread_mutex_lock(
        &resource1
    );

    printf(
        "Thread 1 holds R1 "
        "and requests R2.\n"
    );

    usleep(200000);

    struct timespec limit =
        timeout_after_one_second();

    int result =
        pthread_mutex_timedlock(
            &resource2,
            &limit
        );

    if (result == 0) {
        printf(
            "Thread 1 acquired R2.\n"
        );

        pthread_mutex_unlock(
            &resource2
        );
    } else {
        printf(
            "Thread 1 timed out "
            "waiting for R2.\n"
        );
    }

    pthread_mutex_unlock(
        &resource1
    );

    return NULL;
}

static void *thread2(void *argument)
{
    (void)argument;

    pthread_mutex_lock(
        &resource2
    );

    printf(
        "Thread 2 holds R2 "
        "and requests R1.\n"
    );

    usleep(200000);

    struct timespec limit =
        timeout_after_one_second();

    int result =
        pthread_mutex_timedlock(
            &resource1,
            &limit
        );

    if (result == 0) {
        printf(
            "Thread 2 acquired R1.\n"
        );

        pthread_mutex_unlock(
            &resource1
        );
    } else {
        printf(
            "Thread 2 timed out "
            "waiting for R1.\n"
        );
    }

    pthread_mutex_unlock(
        &resource2
    );

    return NULL;
}

int main(void)
{
    pthread_mutex_init(
        &resource1,
        NULL
    );

    pthread_mutex_init(
        &resource2,
        NULL
    );

    pthread_t first;
    pthread_t second;

    pthread_create(
        &first,
        NULL,
        thread1,
        NULL
    );

    pthread_create(
        &second,
        NULL,
        thread2,
        NULL
    );

    pthread_join(
        first,
        NULL
    );

    pthread_join(
        second,
        NULL
    );

    pthread_mutex_destroy(
        &resource1
    );

    pthread_mutex_destroy(
        &resource2
    );

    printf(
        "Controlled deadlock "
        "demonstration completed.\n"
    );

    return EXIT_SUCCESS;
}
