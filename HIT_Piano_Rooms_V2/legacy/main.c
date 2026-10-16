// 琴房管理系统
// 请仔细阅读操作注意事项：
// 1.请按照注册，预约，签到，签退的步骤进行。
// 2.琴房营业时间为早7点到晚22点，当天21：30以后无法进行预约，请在21：30前进行操作。
// 3.每小时为一个预约时间段，超过半小时不能再预约本时间段的琴房。
// 4.系统只会显示当前时间点可预约的时间段，已经过去的时间段无法预约并且不会显示。
// 5.如果程序出现异常或者已经预约但签到未成功的情况，可能是数据在您的电脑上存储格式有误。
// 此时可以尝试搜索并删除以下三个文件：pianoRooms.txt，reservations.txt，students.txt
// 然后再尝试重新运行程序，重新注册，预约等等
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <ctype.h>

#define MAX_STUDENTS 2000 // 最大学生数量2000人
#define MAX_ROOMS 20      // 最多房间数量20间
#define MAX_LENGTH 50     // 最大长度50

// 学生结构体
typedef struct
{
    char studentId[MAX_LENGTH];  // 学生学号
    char name[MAX_LENGTH];       // 学生名字
    char class1[MAX_LENGTH];     // 学生班级
    char instrument[MAX_LENGTH]; // 学生乐器种类
    char password[MAX_LENGTH];   // 设置密码
    int isRegistered;
} Student;

// 琴房结构体
typedef struct
{
    int roomNumber;
    int isBooked[MAX_ROOMS]; // 用于标记每个时间段琴房是否被预订
} PianoRoom;

// 预约结构体
typedef struct
{
    char studentId[MAX_LENGTH];
    int roomNumber;
    int timeSlot;
    int isSignedIn; // 检查用户是否已经签到
    struct tm startTime;
    struct tm endTime;
    int timeSlotIndex; // 时间段编号，方便用户输入
} Reservation;

// 全局变量
Student students[MAX_STUDENTS];  // 结构体变量
PianoRoom pianoRooms[MAX_ROOMS]; // 结构体变量
Reservation reservations[MAX_STUDENTS];
int studentCount = 0;     // 记录学生总数
int reservationCount = 0; // 记录当前已经存在的预约记录的数量

// 函数声明
void studentRegistration();                  // 学生注册
int findStudentIndex(const char *studentId); // 根据学号查找学生索引函数

void pianoRoomBooking(); // 琴房预约
void pianoRoomSignIn();  // 琴房签到
void pianoRoomSignOut(); // 琴房签退

void viewAnnouncement(); // 查看公告

void saveDataToFile();   // 将数据保存到文件
void loadDataFromFile(); // 从文件加载数据

int findAvailableRooms(int timeSlot, int *availableRooms); // 查找指定时间段空闲琴房函数
void printTimeSlots(int currentHour, int currentMinute);   // 打印时间段函数
void trimWhitespace(char *str);

// 主函数
int main()
{
    int option;

    // 从文件加载数据
    loadDataFromFile();

    do
    {
        printf("*********************************\n");
        printf("*      欢迎使用琴房管理系统     *\n");
        printf("*********************************\n");
        printf("*          1. 学生注册          *\n");
        printf("*          2. 琴房预约          *\n");
        printf("*          3. 琴房签到          *\n");
        printf("*          4. 琴房签退          *\n");
        printf("*          5. 查看公告          *\n");
        printf("*          6. 退出系统          *\n");
        printf("*********************************\n");
        printf("请选择功能: ");
        scanf("%d", &option);

        switch (option)
        {
        case 1:
            studentRegistration();
            break;
        case 2:
            pianoRoomBooking();
            break;
        case 3:
            pianoRoomSignIn();
            break;
        case 4:
            pianoRoomSignOut();
            break;
        case 5:
            viewAnnouncement();
            break;
        case 6:
            printf("已退出系统，欢迎再次使用！\n");
            break;
        default:
            printf("输入错误，请重新输入！\n");
        }
    } while (option != 6);
    return 0;
}

// 学生注册函数
void studentRegistration()
{
    if (studentCount >= MAX_STUDENTS)
    {
        printf("学生数量已达上限，无法注册新学生，请联系管理员。\n");
        return;
    }

    Student newStudent; // 定义一个结构体变量

a:
    printf("请输入学号: ");
    scanf("%49s", newStudent.studentId);

    // 检查学号是否已存在
    if (findStudentIndex(newStudent.studentId) != -1)
    {
        printf("该学号已注册，请重新输入！\n");
        goto a;
    }

    printf("请输入姓名: ");
    scanf("%s", newStudent.name);

    printf("请输入班级: ");
    scanf("%s", newStudent.class1);

    printf("请输入乐器: ");
    scanf("%s", newStudent.instrument);

    printf("请设置密码: ");
    scanf("%s", newStudent.password);

    newStudent.isRegistered = 1;

    students[studentCount] = newStudent;
    studentCount++;
    saveDataToFile();
    printf("注册成功！\n");
}

// 琴房预约函数
void pianoRoomBooking()
{
    char studentId[MAX_LENGTH];
    char password[MAX_LENGTH];
    int timeSlot;
    int availableRooms[MAX_ROOMS];
    int numAvailableRooms;
    int selectedRoom;

    // 获取当前时间
    time_t currentTimeStamp = time(NULL);
    struct tm *currentLocalTime = localtime(&currentTimeStamp);
    int currentHour = currentLocalTime->tm_hour;
    int currentMinute = currentLocalTime->tm_min;

    // 根据当前时间确定起始可预约时间段的小时数（营业时间从7点到21点）
    int startHour = currentHour;
    if (currentMinute >= 30)
    {
        startHour++;
    }

    // 验证学生登录信息并获取可预约时间段信息，若登录失败则直接返回
    while (1)
    {
        // 输入学号和密码并验证登录信息
        printf("请输入学号: ");
        scanf("%s", studentId);

        printf("请输入密码: ");
        scanf("%s", password);

        // 验证学生登录信息
        int studentIndex = findStudentIndex(studentId);
        if (studentIndex != -1 && strcmp(students[studentIndex].password, password) == 0)
        {
            // 登录成功，进入选择时间段的循环
            do
            {
                // 输出每个时间段空闲琴房数
                printf("各时间段空闲琴房数如下：\n");
                printTimeSlots(startHour, 0);

                printf("请输入您要选择预约的时间段的序号（输入数字）: ");

                // 增加对输入合法性的检查，解决输入非数字无限提示问题
                int validInput = 0;
                while (!validInput)
                {
                    if (scanf("%d", &timeSlot) == 1)
                    {
                        validInput = 1;
                    }
                    else
                    {
                        // 清除输入缓冲区中不正确的输入，防止死循环
                        while (getchar() != '\n')
                            ;
                        printf("格式错误请重新输入！\n");
                    }
                }

                // 将输入的时间段序号转换为对应的实际小时数（序号1对应7点）
                int selectedHour = timeSlot + 6;

                // 检查所选时间段是否在当前可预约范围内（不能选择已经过去的时间段且不能超过营业时间）
                if (selectedHour < startHour || selectedHour > 21)
                {
                    printf("无效时间段选择，请重新输入！\n");
                    continue;
                }
                else
                {
                    break;
                }
            } while (1);

            // 当时间段选择成功，跳出外层循环，继续后续的预约流程（查找空闲琴房等）
            break;
        }
        else
        {
            // 登录失败提示并继续外层循环，重新输入学号和密码进行登录验证
            printf("学号或密码错误，登录失败！\n");
        }
    }

    // 查找空闲琴房
    numAvailableRooms = findAvailableRooms(timeSlot, availableRooms);
    if (numAvailableRooms == 0)
    {
        printf("该时间段没有空闲琴房，请重新选择！\n");
        return;
    }

    // 显示空闲琴房号
    printf("当前时间段空闲琴房号如下：\n");
    for (int i = 0; i < numAvailableRooms; i++)
    {
        printf("%d ", availableRooms[i]);
    }
    printf("\n");

    // 选择琴房号并检查是否空闲
    do
    {
        printf("请输入您要预约的琴房号: ");
        scanf("%d", &selectedRoom);

        if (selectedRoom < 1 || selectedRoom > MAX_ROOMS)
        {
            printf("琴房号错误，请重新输入！\n");
        }
        else
        {
            // 检查输入的琴房号是否空闲
            int isRoomAvailable = 0;
            for (int i = 0; i < numAvailableRooms; i++)
            {
                if (availableRooms[i] == selectedRoom)
                {
                    isRoomAvailable = 1;
                    break;
                }
            }

            if (isRoomAvailable == 0) // 说明琴房不空闲
            {
                printf("该琴房号在所选时间段已被预订，请重新输入！\n");
            }
            else
            {
                break;
            }
        }
    } while (1);

    // 确认预约
    printf("是否确认预约？输入1确认，输入0取消: ");
    int confirm;
    scanf("%d", &confirm);

    if (confirm == 1)
    {
        Reservation newReservation;                  // 定义一个结构体变量
        strcpy(newReservation.studentId, studentId); // 将学生信息保存在预约记录里
        newReservation.roomNumber = selectedRoom;
        newReservation.timeSlotIndex = newReservation.timeSlot;
        newReservation.timeSlot = timeSlot;
        // 设置预约开始和结束时间，每个时间段为一小时
        time_t now = time(NULL);
        struct tm *currentTime = localtime(&now);
        // 根据用户选择的时间段序号设置预约开始时间
        newReservation.startTime = *currentTime;
        newReservation.startTime.tm_hour = 7 + timeSlot - 1; // 7点是第一个时间段，通过序号计算对应的小时数
        newReservation.startTime.tm_min = 0;

        newReservation.endTime = newReservation.startTime;
        newReservation.endTime.tm_hour += 1;
        // 检查预约记录是否达到上限，防止数据溢出
        if (reservationCount < MAX_STUDENTS)
        {
            reservations[reservationCount] = newReservation;
            reservationCount++;
        }
        else
        {
            printf("预约记录数量已达上限，无法进行新的预约，请先删除部分预约记录或联系管理员。\n");
        }

        // 更新琴房预订状态
        pianoRooms[selectedRoom - 1].isBooked[timeSlot - 1] = 1; // 又有一个琴房被预定了
        // selectedRoom-1是为了用来存储琴房号，timeSlot - 1是为了用来存储时间段
        printf("预约成功！\n");
    }
    else
    {
        printf("已取消预约！\n");
    }
}

// 去除字符串两端空格的函数
void trimWhitespace(char *str)
{
    int len = strlen(str);
    int start = 0;
    int end = len - 1;

    while (isspace(str[start]) && start < len)
    {
        start++;
    }

    while (isspace(str[end]) && end >= 0)
    {
        end--;
    }

    if (start > 0 || end < len - 1)
    {
        int j = 0;
        for (int i = start; i <= end; i++)
        {
            str[j++] = str[i];
        }
        str[j] = '\0';
    }
}

// 根据学号查找学生索引函数
int findStudentIndex(const char *studentId)
{
    for (int i = 0; i < studentCount; i++)
    {
        if (strcmp(students[i].studentId, studentId) == 0)
        {
            return i;
        }
    }
    return -1;
}

// 琴房签到函数
void pianoRoomSignIn()
{
    char studentId[MAX_LENGTH];
    char name[MAX_LENGTH];
    char password[MAX_LENGTH];

    // 输入姓名并处理格式
    printf("请输入姓名: ");
    scanf("%49s", name);
    trimWhitespace(name);

    // 检查姓名是否为空
    if (name[0] == '\0')
    {
        printf("姓名不能为空，请重新输入！\n");
        return;
    }

    // 输入学号并处理格式
    printf("请输入学号: ");
    scanf("%49s", studentId);
    trimWhitespace(studentId);

    // 检查学号格式，假设学号只包含数字
    for (int i = 0; i < strlen(studentId); i++)
    {
        if (!isdigit(studentId[i]))
        {
            printf("学号格式错误，请重新输入！只允许输入数字。\n");
            return;
        }
    }

    // 输入密码并处理格式
    printf("请输入密码: ");
    scanf("%49s", password);
    trimWhitespace(password);

    // 查找预约记录
    int found = 0;
    for (int i = 0; i < reservationCount; i++)
    {
        // 去除预约记录和输入信息两端可能存在的空格再进行比较，保证程序的准确性
        char trimmedStudentId[MAX_LENGTH];
        strcpy(trimmedStudentId, reservations[i].studentId); // 学生学号
        trimWhitespace(trimmedStudentId);

        char trimmedInputId[MAX_LENGTH];
        strcpy(trimmedInputId, studentId); // 输入的学号
        trimWhitespace(trimmedInputId);

        char trimmedInputPassword[MAX_LENGTH];
        strcpy(trimmedInputPassword, password); // 输入的密码
        trimWhitespace(trimmedInputPassword);

        // 先根据学号找到对应的学生索引
        int studentIndex = findStudentIndex(trimmedStudentId);
        if (studentIndex != -1)
        {
            // 获取对应的学生姓名
            char studentName[MAX_LENGTH];
            strcpy(studentName, students[studentIndex].name);
            trimWhitespace(studentName);

            // 去除学生姓名两端可能存在的空格再进行比较
            char trimmedStudentName[MAX_LENGTH];
            strcpy(trimmedStudentName, studentName);
            trimWhitespace(trimmedStudentName);

            // 比较学号、姓名和密码
            if (strcmp(trimmedInputId, trimmedStudentId) == 0 &&
                strcmp(trimmedStudentName, name) == 0 &&
                strcmp(students[studentIndex].password, trimmedInputPassword) == 0)
            {
                // 新增代码，输出琴房编号
                printf("签到成功，您预约的琴房编号是：%d，预约时间是：%02d:00 - %02d:00，\n请按照预约时间进入琴房，不得提前，谢谢配合。\n",
                       reservations[i].roomNumber,
                       reservations[i].startTime.tm_hour, reservations[i].endTime.tm_hour);
                found = 1;
                reservations[i].isSignedIn = 1; // 设置签到状态为已签到
            }
        }
    }
    if (!found)
    {
        printf("未查询到预约记录，可能是您输入的信息有误或未到签到时间范围，请检查后重新尝试。\n");
    }
}

// 琴房签退函数
void pianoRoomSignOut()
{
    char studentId[MAX_LENGTH];
    char name[MAX_LENGTH];
    printf("请输入姓名: ");
    scanf("%s", name);
    printf("请输入学号: ");
    scanf("%s", studentId);

    // 检查是否签到
    int isSignedIn = 0;
    for (int i = 0; i < reservationCount; i++)
    {
        if (strcmp(reservations[i].studentId, studentId) == 0 && reservations[i].isSignedIn == 1)
        {
            isSignedIn = 1;
            break;
        }
    }

    if (!isSignedIn)
    {
        printf("签退失败，您还未签到！\n");
        return;
    }

    // 查找预约记录
    time_t currentTimeStamp = time(NULL);
    struct tm *currentLocalTime = localtime(&currentTimeStamp);
    int currentHour = currentLocalTime->tm_hour;
    int currentMinute = currentLocalTime->tm_min;

    int found = 0;
    for (int i = 0; i < reservationCount; i++)
    {
        if (strcmp(reservations[i].studentId, studentId) == 0)
        {
            // 计算已使用时间（以分钟为单位）
            int usedMinutes = (currentHour - reservations[i].startTime.tm_hour) * 60 + (currentMinute - reservations[i].startTime.tm_min);
            int allowedMinutes = (reservations[i].endTime.tm_hour - reservations[i].startTime.tm_hour) * 60 + (reservations[i].endTime.tm_min - reservations[i].startTime.tm_min);

            if (usedMinutes <= allowedMinutes)
            {
                printf("签退成功，未超时！\n");
                printf("请带好随身物品，欢迎再次使用！\n");
            }
            else
            {
                int overdueMinutes = usedMinutes - allowedMinutes;
                printf("签退成功，超时 %d 分钟。\n", overdueMinutes);
                printf("请带好随身物品，欢迎再次使用！\n");
            }
            found = 1;
            break;
        }
    }
    if (!found)
    {
        printf("签退失败，您没有签到！\n");
    }
}

// 查看公告函数
void viewAnnouncement()
{
    printf("琴房使用公告：\n\n");
    printf("尊敬的各位使用者：\n\n");
    printf("为了维护琴房的良好秩序与环境，确保每位使用者都能享受到高质量的练习时间，特此发布以下使用规定，请大家共同遵守：\n\n");
    printf("1.预约制度：琴房实行预约使用制度，请提前通过指定渠道（如学校官网、微信公众号等）进行预约，并按时到场使用。未预约者不得进入琴房。\n");
    printf("2.使用时间：琴房每日开放时间为早7:00至晚22:00，请合理安排练习时间，避免超时占用。\n");
    printf("3.爱护设施：请爱护琴房内的各项设施，如钢琴、座椅、节拍器等，使用完毕后请归还原位，并保持整洁。如有损坏，需按价赔偿。\n");
    printf("4.禁止饮食：琴房内禁止食用任何食物或饮料，以保持环境清洁与卫生。\n");
    printf("5.个人物品：请妥善保管好个人物品，如有遗失，责任自负。\n");
    printf("6.遵守规定：请严格遵守琴房的各项规定，如有违反，将视情节轻重给予警告、取消使用资格等处罚。\n\n");
    printf("感谢大家的理解与配合！让我们共同营造一个和谐、有序、高效的琴房环境。\n\n");
    printf("琴房管理办公室\n");
    printf("发布日期：2024年12月1日\n");
}

// 查找指定时间段空闲琴房函数
int findAvailableRooms(int timeSlot, int *availableRooms)
{ // count返回可用房间数量，指针数组availableRooms储存可用房间的房间号
    int count = 0;
    for (int i = 0; i < MAX_ROOMS; i++)
    {
        if (!pianoRooms[i].isBooked[timeSlot - 1])
        {
            availableRooms[count] = i + 1; // i+1是琴房的编号
            count++;
        }
    }
    return count;
}

// 打印时间段函数,营业时间早七点到晚十点
void printTimeSlots(int currentHour, int currentMinute)
{
    // 根据当前时间确定起始显示的时间点
    int startHour = (currentHour < 7) ? 7 : currentHour;
    int startMinute = currentMinute;

    // 如果当前分钟数大于等于30，将起始小时数加1，且起始分钟数设为0
    if (currentMinute >= 30)
    {
        startHour++;
        startMinute = 0;
    }

    // 如果起始小时数达到22（晚上10点，因为营业时间到晚上10点），则不再显示任何空闲时间段
    if (startHour >= 22)
    {
        return;
    }

    printf("序号\t时间段\t\t空闲琴房个数\n");
    for (int i = startHour; i <= 21; i++)
    {
        int availableRooms[MAX_ROOMS];
        int numAvailableRooms = findAvailableRooms(i, availableRooms);
        printf("%d\t%d:00——%d:00\t%d\n", i - 6, i, i + 1, numAvailableRooms);
    }
}

// 将数据保存到文件函数
void saveDataToFile()
{
    FILE *fp;

    // 保存学生数据
    fp = fopen("students.txt", "w"); // 写入
    if (fp == NULL)
    { // 文件打开失败
        printf("无法打开文件保存学生数据！\n");
        return;
    }
    for (int i = 0; i < studentCount; i++)
    {
        fprintf(fp, "%s %s %s %s %s %d\n",
                students[i].studentId,
                students[i].name,
                students[i].class1,
                students[i].instrument,
                students[i].password,
                students[i].isRegistered);
    }
    fclose(fp);

    // 保存预约数据
    fp = fopen("reservations.txt", "w");
    if (fp == NULL)
    {
        printf("无法打开文件保存预约数据！\n");
        return;
    }
    for (int i = 0; i < reservationCount; i++)
    {
        fprintf(fp, "%s %d %d %d-%d-%d %d-%d-%d\n",
                reservations[i].studentId,
                reservations[i].roomNumber,
                reservations[i].timeSlot,
                reservations[i].startTime.tm_year + 1900, // 预约开始时间
                reservations[i].startTime.tm_mon + 1,     // 开始的月份
                reservations[i].startTime.tm_mday,        // 开始日期
                reservations[i].endTime.tm_year + 1900,   // 预约结束时间
                reservations[i].endTime.tm_mon + 1,       // 结束的月份
                reservations[i].endTime.tm_mday);         // 结束日期
    }
    fclose(fp);

    // 保存琴房数据，这里只是保存预订状态
    fp = fopen("pianoRooms.txt", "w");
    if (fp == NULL)
    {
        printf("无法打开文件保存琴房数据！\n");
        return;
    }
    for (int i = 0; i < MAX_ROOMS; i++)
    {
        for (int j = 0; j < 24; j++)
        {
            fprintf(fp, "%d ", pianoRooms[i].isBooked[j]);
        }
        fprintf(fp, "\n");
    }
    fclose(fp);
}

// 从文件加载数据函数
void loadDataFromFile()
{
    FILE *fp;

    // 加载学生数据
    fp = fopen("students.txt", "r");
    if (fp != NULL)
    {
        studentCount = 0;
        while (fscanf(fp, "%s %s %s %s %s %d\n",
                      students[studentCount].studentId,
                      students[studentCount].name,
                      students[studentCount].class1,
                      students[studentCount].instrument,
                      students[studentCount].password,
                      &students[studentCount].isRegistered) != EOF &&
               studentCount < MAX_STUDENTS)
        {
            studentCount++;
        }
        fclose(fp);
    }

    // 加载预约数据
    fp = fopen("reservations.txt", "r");
    if (fp != NULL)
    {
        reservationCount = 0;
        while (fscanf(fp, "%s %d %d %d-%d-%d %d-%d-%d\n",
                      reservations[reservationCount].studentId,
                      reservations[reservationCount].roomNumber,
                      reservations[reservationCount].timeSlot,
                      &reservations[reservationCount].startTime.tm_year + 1900,
                      &reservations[reservationCount].startTime.tm_mon + 1,
                      &reservations[reservationCount].startTime.tm_mday,
                      &reservations[reservationCount].endTime.tm_year + 1900,
                      &reservations[reservationCount].endTime.tm_mon + 1,
                      &reservations[reservationCount].endTime.tm_mday) != EOF &&
               reservationCount < MAX_STUDENTS)
        {
            reservationCount++;
        }
        fclose(fp);
    }

    // 加载琴房数据
    fp = fopen("pianoRooms.txt", "r");
    if (fp != NULL)
    {
        for (int i = 0; i < MAX_ROOMS; i++)
        {
            for (int j = 0; j < 24; j++)
            {
                fscanf(fp, "%d ", &pianoRooms[i].isBooked[j]);
            }
        }
        fclose(fp);
    }
}