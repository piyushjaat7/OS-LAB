
#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>
#include <semaphore.h>
#include <unistd.h>

#define BUFFER_SIZE 4
#define ITEM_COUNT 10

static int buffer[BUFFER_SIZE];
static int input_index = 0;
static int output_index = 0;

static pthread_mutex_t buffer_mutex;
static sem_t empty_slots;
static sem_t full_slots;

static void *producer(void *argument)
{
    (void)argument;

    for (int item = 1; item <= ITEM_COUNT; ++item) {
        if (sem_wait(&empty_slots) == -1) {
            perror("sem_wait empty");
            return NULL;
        }

        if (pthread_mutex_lock(&buffer_mutex) != 0) {
            fprintf(stderr, "Producer mutex lock failed.\n");
            sem_post(&empty_slots);
            return NULL;
        }

        buffer[input_index] = item;

        printf(
            "Produced %d at position %d\n",
            item,
            input_index
        );

        input_index = (input_index + 1) % BUFFER_SIZE;

        pthread_mutex_unlock(&buffer_mutex);

        sem_post(&full_slots);

        usleep(50000);
    }

    return NULL;
}

static void *consumer(void *argument)
{
    (void)argument;

    for (int count = 0; count < ITEM_COUNT; ++count) {
        if (sem_wait(&full_slots) == -1) {
            perror("sem_wait full");
            return NULL;
        }

        if (pthread_mutex_lock(&buffer_mutex) != 0) {
            fprintf(stderr, "Consumer mutex lock failed.\n");
            sem_post(&full_slots);
            return NULL;
        }

        int item = buffer[output_index];

        printf(
            "Consumed %d from position %d\n",
            item,
            output_index
        );

        output_index = (output_index + 1) % BUFFER_SIZE;

        pthread_mutex_unlock(&buffer_mutex);

        sem_post(&empty_slots);

        usleep(80000);
    }

    return NULL;
}

int main(void)
{
    if (pthread_mutex_init(&buffer_mutex, NULL) != 0) {
        fprintf(stderr, "Mutex initialization failed.\n");
        return EXIT_FAILURE;
    }

    if (sem_init(&empty_slots, 0, BUFFER_SIZE) == -1) {
        perror("sem_init empty");
        pthread_mutex_destroy(&buffer_mutex);
        return EXIT_FAILURE;
    }

    if (sem_init(&full_slots, 0, 0) == -1) {
        perror("sem_init full");
        sem_destroy(&empty_slots);
        pthread_mutex_destroy(&buffer_mutex);
        return EXIT_FAILURE;
    }

    pthread_t producer_id;
    pthread_t consumer_id;

    if (pthread_create(&producer_id, NULL, producer, NULL) != 0) {
        fprintf(stderr, "Producer creation failed.\n");
        sem_destroy(&full_slots);
        sem_destroy(&empty_slots);
        pthread_mutex_destroy(&buffer_mutex);
        return EXIT_FAILURE;
    }

    if (pthread_create(&consumer_id, NULL, consumer, NULL) != 0) {
        fprintf(stderr, "Consumer creation failed.\n");

        /*
         * The producer may be waiting for an empty slot.
         * Cancel and join it before destroying synchronization objects.
         */
        pthread_cancel(producer_id);
        pthread_join(producer_id, NULL);

        sem_destroy(&full_slots);
        sem_destroy(&empty_slots);
        pthread_mutex_destroy(&buffer_mutex);
        return EXIT_FAILURE;
    }

    pthread_join(producer_id, NULL);
    pthread_join(consumer_id, NULL);

    sem_destroy(&empty_slots);
    sem_destroy(&full_slots);
    pthread_mutex_destroy(&buffer_mutex);

    printf("Producer-Consumer completed.\n");

    return EXIT_SUCCESS;
}
