
#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>
#include <semaphore.h>
#include <unistd.h>

#define READER_COUNT 3
#define WRITER_COUNT 2
#define PHILOSOPHER_COUNT 5

static int shared_value = 0;
static int active_readers = 0;

static pthread_mutex_t reader_mutex;
static pthread_mutex_t resource_mutex;

static pthread_mutex_t forks[PHILOSOPHER_COUNT];

static sem_t waiter;

static void *reader(void *argument)
{
    long id = (long)argument;

    for (int round = 1; round <= 2; ++round) {
        pthread_mutex_lock(&reader_mutex);

        active_readers++;

        if (active_readers == 1) {
            pthread_mutex_lock(&resource_mutex);
        }

        pthread_mutex_unlock(&reader_mutex);

        printf(
            "Reader %ld read value %d in round %d\n",
            id,
            shared_value,
            round
        );

        usleep(40000);

        pthread_mutex_lock(&reader_mutex);

        active_readers--;

        if (active_readers == 0) {
            pthread_mutex_unlock(&resource_mutex);
        }

        pthread_mutex_unlock(&reader_mutex);

        usleep(30000);
    }

    return NULL;
}

static void *writer(void *argument)
{
    long id = (long)argument;

    for (int round = 1; round <= 2; ++round) {
        pthread_mutex_lock(&resource_mutex);

        shared_value++;

        printf(
            "Writer %ld wrote value %d in round %d\n",
            id,
            shared_value,
            round
        );

        usleep(50000);

        pthread_mutex_unlock(&resource_mutex);

        usleep(35000);
    }

    return NULL;
}

static void *philosopher(void *argument)
{
    long id = (long)argument;

    int left = (int)id;
    int right = ((int)id + 1) % PHILOSOPHER_COUNT;

    printf("Philosopher %ld is thinking.\n", id);

    usleep(30000);

    sem_wait(&waiter);

    pthread_mutex_lock(&forks[left]);
    pthread_mutex_lock(&forks[right]);

    printf(
        "Philosopher %ld is eating using forks %d and %d.\n",
        id,
        left,
        right
    );

    usleep(50000);

    pthread_mutex_unlock(&forks[right]);
    pthread_mutex_unlock(&forks[left]);

    sem_post(&waiter);

    printf("Philosopher %ld finished eating.\n", id);

    return NULL;
}

int main(void)
{
    if (pthread_mutex_init(&reader_mutex, NULL) != 0) {
        fprintf(stderr, "Reader mutex initialization failed.\n");
        return EXIT_FAILURE;
    }

    if (pthread_mutex_init(&resource_mutex, NULL) != 0) {
        fprintf(stderr, "Resource mutex initialization failed.\n");
        pthread_mutex_destroy(&reader_mutex);
        return EXIT_FAILURE;
    }

    pthread_t readers[READER_COUNT];
    pthread_t writers[WRITER_COUNT];

    for (long i = 0; i < READER_COUNT; ++i) {
        if (pthread_create(&readers[i], NULL, reader, (void *)i) != 0) {
            fprintf(stderr, "Reader thread creation failed.\n");
            return EXIT_FAILURE;
        }
    }

    for (long i = 0; i < WRITER_COUNT; ++i) {
        if (pthread_create(&writers[i], NULL, writer, (void *)i) != 0) {
            fprintf(stderr, "Writer thread creation failed.\n");
            return EXIT_FAILURE;
        }
    }

    for (int i = 0; i < READER_COUNT; ++i) {
        pthread_join(readers[i], NULL);
    }

    for (int i = 0; i < WRITER_COUNT; ++i) {
        pthread_join(writers[i], NULL);
    }

    printf(
        "Readers-Writers completed. Final value = %d\n",
        shared_value
    );

    pthread_mutex_destroy(&reader_mutex);
    pthread_mutex_destroy(&resource_mutex);

    if (sem_init(&waiter, 0, PHILOSOPHER_COUNT - 1) == -1) {
        perror("sem_init waiter");
        return EXIT_FAILURE;
    }

    for (int i = 0; i < PHILOSOPHER_COUNT; ++i) {
        if (pthread_mutex_init(&forks[i], NULL) != 0) {
            fprintf(stderr, "Fork mutex initialization failed.\n");
            return EXIT_FAILURE;
        }
    }

    pthread_t philosophers[PHILOSOPHER_COUNT];

    for (long i = 0; i < PHILOSOPHER_COUNT; ++i) {
        if (pthread_create(
                &philosophers[i],
                NULL,
                philosopher,
                (void *)i
            ) != 0) {
            fprintf(stderr, "Philosopher thread creation failed.\n");
            return EXIT_FAILURE;
        }
    }

    for (int i = 0; i < PHILOSOPHER_COUNT; ++i) {
        pthread_join(philosophers[i], NULL);
    }

    for (int i = 0; i < PHILOSOPHER_COUNT; ++i) {
        pthread_mutex_destroy(&forks[i]);
    }

    sem_destroy(&waiter);

    printf("Dining Philosophers completed without deadlock.\n");

    return EXIT_SUCCESS;
}
