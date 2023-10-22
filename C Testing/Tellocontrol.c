#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <arpa/inet.h>
#include <netinet/in.h>
#include <sys/socket.h>
#include <unistd.h>

#define TELLO_IP "192.168.10.1"
#define TELLO_PORT 8889

int main() {
    int sockfd;
    struct sockaddr_in droneAddr;
    char message[] = "command";

    // Create a UDP socket
    sockfd = socket(AF_INET, SOCK_DGRAM, 0);
    if (sockfd < 0) {
        perror("Error opening socket");
        return 1;
    }

    memset(&droneAddr, 0, sizeof(droneAddr));
    droneAddr.sin_family = AF_INET;
    droneAddr.sin_port = htons(TELLO_PORT);
    droneAddr.sin_addr.s_addr = inet_addr(TELLO_IP);

    // Send the "command" message to Tello
    if (sendto(sockfd, message, strlen(message), 0, (struct sockaddr*)&droneAddr, sizeof(droneAddr)) < 0) {
        perror("Error sending command");
        close(sockfd);
        return 1;
    }

    printf("Sent 'command' to Tello. You can now send more commands or receive responses.\n");

    close(sockfd);
    return 0;
}
