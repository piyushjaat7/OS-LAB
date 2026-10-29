#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>

#define THREADS 2
#define INCREMENTS 1000000

static long unsafe_counter = 0;
static long safe_counter = 0;
static pthread_mutex_t counter_mutex;

static void *unsafe_worker(void *argument)
{
    (void)argument;

    for (long i = 0; i < INCREMENTS; ++i) {
        unsafe_counter++;
    }

    return NULL;
}

static void *safe_worker(void *argument)
{
    (void)argument;

    for (long i = 0; i < INCREMENTS; ++i) {
        if (pthread_mutex_lock(&counter_mutex) != 0) {
            fprintf(stderr, "Mutex lock failed.\n");
            return NULL;
        }

        safe_counter++;

        if (pthread_mutex_unlock(&counter_mutex) != 0) {
            fprintf(stderr, "Mutex unlock failed.\n");
            return NULL;
        }
    }

    return NULL;
}

static int run_workers(void *(*worker)(void *))
{
    pthread_t ids[THREADS];

    for (int i = 0; i < THREADS; ++i) {
        if (pthread_create(&ids[i], NULL, worker, NULL) != 0) {
            fprintf(stderr, "Thread creation failed.\n");
            return -1;
        }
    }

    for (int i = 0; i < THREADS; ++i) {
        if (pthread_join(ids[i], NULL) != 0) {
            fprintf(stderr, "Thread join failed.\n");
            return -1;
        }
    }

    return 0;
}

int main(void)
{
    const long expected = THREADS * INCREMENTS;

    if (run_workers(unsafe_worker) != 0) {
        return EXIT_FAILURE;
    }

    printf("Unsafe expected: %ld\n", expected);
    printf("Unsafe actual:   %ld\n", unsafe_counter);

    if (pthread_mutex_init(&counter_mutex, NULL) != 0) {
        fprintf(stderr, "Mutex initialization failed.\n");
        return EXIT_FAILURE;
    }

    if (run_workers(safe_worker) != 0) {
        pthread_mutex_destroy(&counter_mutex);
        return EXIT_FAILURE;
    }

    printf("Mutex expected:  %ld\n", expected);
    printf("Mutex actual:    %ld\n", safe_counter);

    if (pthread_mutex_destroy(&counter_mutex) != 0) {
        fprintf(stderr, "Mutex destruction failed.\n");
        return EXIT_FAILURE;
    }

    return EXIT_SUCCESS;
}