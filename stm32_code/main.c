/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file           : main.c
  * @brief          : Main program body
  ******************************************************************************
  * @attention
  *
  * Copyright (c) 2026 STMicroelectronics.
  * All rights reserved.
  *
  * This software is licensed under terms that can be found in the LICENSE file
  * in the root directory of this software component.
  * If no LICENSE file comes with this software, it is provided AS-IS.
  *
  ******************************************************************************
  */
/* USER CODE END Header */
/* Includes ------------------------------------------------------------------*/
#include "main.h"

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */
#include <stdio.h>
#include <string.h>
/* USER CODE END Includes */

/* Private typedef -----------------------------------------------------------*/
/* USER CODE BEGIN PTD */

/* USER CODE END PTD */

/* Private define ------------------------------------------------------------*/
/* USER CODE BEGIN PD */

/* USER CODE END PD */

/* Private macro -------------------------------------------------------------*/
/* USER CODE BEGIN PM */

/* USER CODE END PM */

/* Private variables ---------------------------------------------------------*/
ADC_HandleTypeDef hadc1;

TIM_HandleTypeDef htim1;
TIM_HandleTypeDef htim2;

UART_HandleTypeDef huart1;

/* USER CODE BEGIN PV */
char msg[50];
////////LDR/////////////
int track;
uint32_t ldr = 0;
int count=0;
//////////encoder////////
 uint8_t currentCLK = 0;
 uint8_t lastCLK = 0;
 int counter = 0;
 int clicked = 0;

/* RGB STATE */
uint8_t rgbState = 0;
char status[20];

/* DHT11 */
uint8_t RHI, RHD, TCI, TCD, SUM;
uint32_t pMillis, cMillis;
float tFahrenheit = 0;
float tCelsius = 0;
float RH = 0;

/* USER CODE END PV */

/* Private function prototypes -----------------------------------------------*/
void SystemClock_Config(void);
static void MX_GPIO_Init(void);
static void MX_ADC1_Init(void);
static void MX_TIM1_Init(void);
static void MX_TIM2_Init(void);
static void MX_USART1_UART_Init(void);
/* USER CODE BEGIN PFP */

/* USER CODE END PFP */

/* Private user code ---------------------------------------------------------*/
/* USER CODE BEGIN 0 */
#define DHT11_PORT GPIOB
#define DHT11_PIN GPIO_PIN_9


void microDelay(uint16_t delay)
{
    __HAL_TIM_SET_COUNTER(&htim2, 0);
    while (__HAL_TIM_GET_COUNTER(&htim2) < delay);
}

uint8_t DHT11_Start(void)
{
    uint8_t Response = 0;
    GPIO_InitTypeDef GPIO_InitStructPrivate = {0};

    GPIO_InitStructPrivate.Pin = DHT11_PIN;
    GPIO_InitStructPrivate.Mode = GPIO_MODE_OUTPUT_PP;
    GPIO_InitStructPrivate.Speed = GPIO_SPEED_FREQ_LOW;
    GPIO_InitStructPrivate.Pull = GPIO_NOPULL;

    HAL_GPIO_Init(DHT11_PORT, &GPIO_InitStructPrivate);

    HAL_GPIO_WritePin(DHT11_PORT, DHT11_PIN, GPIO_PIN_RESET);
    HAL_Delay(20);

    HAL_GPIO_WritePin(DHT11_PORT, DHT11_PIN, GPIO_PIN_SET);
    microDelay(30);

    GPIO_InitStructPrivate.Mode = GPIO_MODE_INPUT;
    GPIO_InitStructPrivate.Pull = GPIO_PULLUP;

    HAL_GPIO_Init(DHT11_PORT, &GPIO_InitStructPrivate);

    microDelay(40);

    if (!(HAL_GPIO_ReadPin(DHT11_PORT, DHT11_PIN)))
    {
        microDelay(80);

        if ((HAL_GPIO_ReadPin(DHT11_PORT, DHT11_PIN)))
            Response = 1;
    }

    pMillis = HAL_GetTick();
    cMillis = HAL_GetTick();

    while ((HAL_GPIO_ReadPin(DHT11_PORT, DHT11_PIN)) && pMillis + 2 > cMillis)
    {
        cMillis = HAL_GetTick();
    }

    return Response;
}

uint8_t DHT11_Read(void)
{
    uint8_t a, b = 0;

    for (a = 0; a < 8; a++)
    {
        pMillis = HAL_GetTick();
        cMillis = HAL_GetTick();

        while (!(HAL_GPIO_ReadPin(DHT11_PORT, DHT11_PIN)) && pMillis + 2 > cMillis)
        {
            cMillis = HAL_GetTick();
        }

        microDelay(40);

        if (!(HAL_GPIO_ReadPin(DHT11_PORT, DHT11_PIN)))
            b &= ~(1 << (7 - a));
        else
            b |= (1 << (7 - a));

        pMillis = HAL_GetTick();
        cMillis = HAL_GetTick();

        while ((HAL_GPIO_ReadPin(DHT11_PORT, DHT11_PIN)) && pMillis + 2 > cMillis)
        {
            cMillis = HAL_GetTick();
        }
    }

    return b;
}
int _write(int file,
           char *ptr,
           int len)
{
    HAL_UART_Transmit(&huart1,
                      (uint8_t*)ptr,
                      len,
                      HAL_MAX_DELAY);

    return len;
}

/* USER CODE END 0 */

/**
  * @brief  The application entry point.
  * @retval int
  */
int main(void)
{

  /* USER CODE BEGIN 1 */

  /* USER CODE END 1 */

  /* MCU Configuration--------------------------------------------------------*/

  /* Reset of all peripherals, Initializes the Flash interface and the Systick. */
	HAL_Init();

  /* USER CODE BEGIN Init */

  /* USER CODE END Init */

  /* Configure the system clock */
  SystemClock_Config();

  /* USER CODE BEGIN SysInit */

  /* USER CODE END SysInit */

  /* Initialize all configured peripherals */
  MX_GPIO_Init();
  MX_ADC1_Init();
  MX_TIM1_Init();
  MX_TIM2_Init();
  MX_USART1_UART_Init();
  /* USER CODE BEGIN 2 */
  /* START PWM */
  HAL_TIM_PWM_Start(&htim1, TIM_CHANNEL_2);
  HAL_TIM_PWM_Start(&htim1, TIM_CHANNEL_3);
  HAL_TIM_PWM_Start(&htim1, TIM_CHANNEL_4);

  /* =========================
     START TIM2
     ========================= */

  HAL_TIM_Base_Start(&htim2);

  /* INITIAL ENCODER STATE */
  lastCLK = HAL_GPIO_ReadPin(GPIOB,GPIO_PIN_10);
  /* USER CODE END 2 */

  /* Infinite loop */
  /* USER CODE BEGIN WHILE */
  while (1)
    /* USER CODE END WHILE */
  {
    /* USER CODE BEGIN 3 */
	  /* =========================
	//		           DHT11 SENSOR
	//		           ========================= */
		  static uint32_t dhtTimer = 0;

		  if(HAL_GetTick() - dhtTimer >= 2000)
		  {
		      dhtTimer = HAL_GetTick();
			  if (DHT11_Start())
			  	      {
			  	          RHI = DHT11_Read();
			  	          RHD = DHT11_Read();
			  	          TCI = DHT11_Read();
			  	          TCD = DHT11_Read();
			  	          SUM = DHT11_Read();

			  	          if (RHI + RHD + TCI + TCD == SUM)
			  	          {
			  	              tCelsius = (float)TCI + (float)(TCD / 10.0);
			  	              tFahrenheit = tCelsius * 9 / 5 + 32;
			  	              RH = (float)RHI + (float)(RHD / 10.0);

			  	              // Use tCelsius, tFahrenheit, RH here
//			  	            char buf[50];

//			  	            sprintf(buf,
//			  	                    "TEMP:%d\r\n",
//			  	                    (int)tCelsius);
//
//			  	            HAL_UART_Transmit(&huart1,
//			  	                              (uint8_t*)buf,
//			  	                              strlen(buf),
//			  	                              100);
//
//
//			  	            sprintf(buf,
//			  	                    "HUM:%d\r\n",
//			  	                    (int)RH);
//
//			  	            HAL_UART_Transmit(&huart1,
//			  	                              (uint8_t*)buf,
//			  	                              strlen(buf),
//			  	                              100);
			  //				  sprintf(buf,"n2.val=125");
			  //				  HAL_UART_Transmit(&huart1,(uint8_t*)buf,strlen(buf),100);
			  //				  HAL_UART_Transmit(&huart1,end_cmd,3,100);
			  	          }
			  	      }
		  }
			  	        /* =========================
			  	           LDR SENSOR
			  	           ========================= */

			  	        HAL_ADC_Start(&hadc1);

			  	        HAL_ADC_PollForConversion(&hadc1,
			  	                                  100);

			  	        ldr = HAL_ADC_GetValue(&hadc1);


			  	        /* =========================
			  	           TRACKING SENSOR
			  	           ========================= */

			  	        track = HAL_GPIO_ReadPin(GPIOB,
			  	                                 GPIO_PIN_0);
			  	      /* =========================
			  	         SYSTEM STATUS
			  	         ========================= */

			  	      if(track == GPIO_PIN_RESET)
			  	      {
			  	          strcpy(status, "INTRUSION");
			  	      }
			  	      else if(tCelsius >= 35)
			  	      {
			  	          strcpy(status, "WARNING");
			  	      }
			  	      else
			  	      {
			  	          strcpy(status, "NORMAL");
			  	      }

			  	        /* =========================
			  	           PRIORITY 1:
			  	           INTRUSION DETECTED
			  	           ========================= */

			  	        /* =========================
			  	           INTRUSION DETECTED
			  	           ========================= */

			  	        if(track == GPIO_PIN_RESET)
			  	        {
			  	            /* RESET RGB STATE */

			  	            rgbState = 0;

			  	            /* BUZZER ON */

			  	            HAL_GPIO_WritePin(GPIOB,
			  	                              GPIO_PIN_5,
			  	                              GPIO_PIN_SET);
//			  	          printf("RGB:%d\r\n", rgbState);
//			  	          printf("TRACK:%d\r\n", track);

			  	            /* RED */

			  	            __HAL_TIM_SET_COMPARE(&htim1,
			  	                                  TIM_CHANNEL_2,
			  	                                  1000);

			  	            __HAL_TIM_SET_COMPARE(&htim1,
			  	                                  TIM_CHANNEL_3,
			  	                                  0);

			  	            __HAL_TIM_SET_COMPARE(&htim1,
			  	                                  TIM_CHANNEL_4,
			  	                                  0);
			  	        }
			  	        /* =========================
			  	           NO INTRUSION
			  	           ========================= */

			  	        else
			  	        {

			  	            /* BUZZER OFF */

			  	            HAL_GPIO_WritePin(GPIOB,
			  	                              GPIO_PIN_5,
			  	                              GPIO_PIN_RESET);
//			  	            rgbState = 0;



			  	            /* =========================
			  	               BRIGHT -> RED
			  	               ========================= */

			  	            if(ldr > 3200 &&
			  	               rgbState != 1)
			  	            {
			  	                rgbState = 1;

			  	                __HAL_TIM_SET_COMPARE(&htim1,
			  	                                      TIM_CHANNEL_2,
			  	                                      1000);

			  	                __HAL_TIM_SET_COMPARE(&htim1,
			  	                                      TIM_CHANNEL_3,
			  	                                      0);

			  	                __HAL_TIM_SET_COMPARE(&htim1,
			  	                                      TIM_CHANNEL_4,
			  	                                      0);
//			  	              printf("RGB:%d\r\n", rgbState);
			  	            }


			  	            /* =========================
			  	               NORMAL -> GREEN
			  	               ========================= */

			  	            else if(ldr > 200 &&
			  	                    ldr < 3000 &&
			  	                    rgbState != 2)
			  	            {
			  	                rgbState = 2;

			  	                __HAL_TIM_SET_COMPARE(&htim1,
			  	                                      TIM_CHANNEL_2,
			  	                                      0);

			  	                __HAL_TIM_SET_COMPARE(&htim1,
			  	                                      TIM_CHANNEL_3,
			  	                                      1000);

			  	                __HAL_TIM_SET_COMPARE(&htim1,
			  	                                      TIM_CHANNEL_4,
			  	                                      0);
//			  	              printf("RGB:%d\r\n", rgbState);
			  	            }


			  	            /* =========================
			  	               DARK -> BLUE
			  	               ========================= */

			  	            else if(ldr < 200 &&
			  	                    rgbState != 3)
			  	            {
			  	                rgbState = 3;

			  	                __HAL_TIM_SET_COMPARE(&htim1,
			  	                                      TIM_CHANNEL_2,
			  	                                      0);

			  	                __HAL_TIM_SET_COMPARE(&htim1,
			  	                                      TIM_CHANNEL_3,
			  	                                      0);

			  	                __HAL_TIM_SET_COMPARE(&htim1,
			  	                                      TIM_CHANNEL_4,
			  	                                      1000);
//			  	              printf("RGB:%d\r\n", rgbState);


			  	            }
			  	        }
			  	      /* =========================
			  	         RGB UART PRINT
			  	         ========================= */

//			  	      if(rgbState != oldRGB)
//			  	      {
//			  	          printf("RGB:%d\r\n",
//			  	                 rgbState);
//
//			  	          oldRGB = rgbState;
//			  	          HAL_Delay(5);
//			  	      }


			  	      /* =========================
			  	         TRACK UART PRINT
			  	         ========================= */
//
//			  	      if(track != oldTrack)
//			  	      {
//			  	          printf("TRACK:%d\r\n",
//			  	                 track);
//
//			  	          oldTrack = track;
//			  	          HAL_Delay(5);
//			  	      }
//			  	        /* =========================
//	//		  	           ROTARY ENCODER  code 1- working code
//	//		  	           ========================= */
//	//
//			  	        currentCLK = HAL_GPIO_ReadPin(GPIOB,
//			  	                                      GPIO_PIN_10);
//
//			  	        if(currentCLK != lastCLK)
//			  	        {
//			  	            if(HAL_GPIO_ReadPin(GPIOB,
//			  	                                GPIO_PIN_11)
//			  	               == currentCLK)
//			  	            {
//			  	                counter++;
//			  	              printf("ENC:%d\r\n", counter);
//			  	            }
//			  	            else
//			  	            {
//			  	                counter--;
//			  	              printf("ENC:%d\r\n", counter);
//			  	            }
//			  	        }
////
////			  	        lastCLK = currentCLK;
//			  	      currentCLK = HAL_GPIO_ReadPin(GPIOB, GPIO_PIN_10);
//
//			  	      if(currentCLK != lastCLK)
//			  	      {
//			  	          /* READ DT IMMEDIATELY — same moment as CLK edge */
//			  	          uint8_t currentDT = HAL_GPIO_ReadPin(GPIOB, GPIO_PIN_11);
//
//			  	          if(currentCLK == GPIO_PIN_SET)   /* RISING EDGE ONLY */
//			  	          {
//			  	              if(currentDT != currentCLK)  /* DT LOW when CLK rises = CW */
//			  	              {
//			  	                  counter++;
//			  	                  printf("ENC:%d\r\n", counter);
//			  	              }
//			  	              else                          /* DT HIGH when CLK rises = CCW */
//			  	              {
//			  	                  counter--;
//			  	                  printf("ENC:%d\r\n", counter);
//			  	              }
//			  	          }
//			  	      }
//
//			  	      lastCLK = currentCLK;
//	//
			  	      /* =========================
			  	         ROTARY ENCODER
			  	         ========================= */
//
////			  	      static uint8_t lastCLK = 0;
//
//			  	      uint8_t currentCLK =
//			  	          HAL_GPIO_ReadPin(
//			  	              GPIOB,
//			  	              GPIO_PIN_10
//			  	          );
//
//			  	      /* RISING EDGE DETECTION */
//
//			  	      if(currentCLK != lastCLK &&
//			  	         currentCLK == GPIO_PIN_SET)
//			  	      {
//			  	          /* CLOCKWISE */
//
//			  	          if(HAL_GPIO_ReadPin(
//			  	                 GPIOB,
//			  	                 GPIO_PIN_11
//			  	             ) == currentCLK)
//			  	          {
//			  	              counter++;
//
//			  	              printf(
//			  	                  "ENC:%d\r\n",
//			  	                  counter
//			  	              );
//			  	          }
//
//			  	          /* ANTICLOCKWISE */
//
//			  	          else
//			  	          {
//			  	              counter--;
//
//			  	              printf(
//			  	                  "ENC:%d\r\n",
//			  	                  counter
//			  	              );
//			  	          }
//
//			  	          HAL_Delay(1);
//			  	      }
//
//			  	      lastCLK = currentCLK;
	////		  	      /* =========================
	//		  	         ENCODER BUTTON
	//		  	         ========================= */
	//
	//		  	      static uint8_t lastButtonState = GPIO_PIN_SET;
	//
	//		  	      uint8_t currentButtonState =
	//		  	      HAL_GPIO_ReadPin(GPIOB, GPIO_PIN_12);
	//
	//		  	      if(currentButtonState == GPIO_PIN_RESET &&
	//		  	         lastButtonState == GPIO_PIN_SET)
	//		  	      {
	//		  	          HAL_Delay(20);
	//
	//		  	          if(HAL_GPIO_ReadPin(GPIOB, GPIO_PIN_12)
	//		  	             == GPIO_PIN_RESET)
	//		  	          {
	//		  	              clicked++;
	//
	//		  	              printf("Clicked = %d\r\n", clicked);
	//		  	          }
	//		  	      }
	//
	//		  	      lastButtonState = currentButtonState;
	//		  	      HAL_Delay(10);

			  	      /* =========================
			  	         ENCODER BUTTON
//			  	         ========================= */
//
//
//			  	      if(HAL_GPIO_ReadPin(GPIOB,
//			  	                          GPIO_PIN_12)
//			  	         == GPIO_PIN_RESET)
//			  	      {
//			  	          HAL_Delay(20);
//
//			  	          if(HAL_GPIO_ReadPin(GPIOB,
//			  	                              GPIO_PIN_12)
//			  	             == GPIO_PIN_RESET)
//			  	          {
//			  	              clicked++;
//			  	            printf("BTN:%d\r\n", clicked);
//
//			  	              while(HAL_GPIO_ReadPin(GPIOB,
//			  	                                     GPIO_PIN_12)
//			  	                    == GPIO_PIN_RESET);
//			  	          }
//			  	      }
////				  else
////			  	    {
////			  	        clicked = 0;
////			  	    }
			  	      /* =========================
			  	         ROTARY ENCODER
			  	         ========================= */
//
//			  	      static uint32_t encoderDebounce = 0;
//
//			  	      currentCLK = HAL_GPIO_ReadPin(
//			  	          GPIOB,
//			  	          GPIO_PIN_11
//			  	      );
//
//			  	      if(currentCLK != lastCLK)
//			  	      {
//			  	          if(HAL_GetTick() - encoderDebounce > 2)
//			  	          {
//			  	              if(HAL_GPIO_ReadPin(
//			  	                     GPIOB,
//			  	                     GPIO_PIN_10
//			  	                 ) == currentCLK)
//			  	              {
//			  	                  counter--;
//
//			  	                  printf(
//			  	                      "ENC:%d\r\n",
//			  	                      counter
//			  	                  );
//			  	              }
//			  	              else
//			  	              {
//			  	                  counter++;
//
//			  	                  printf(
//			  	                      "ENC:%d\r\n",
//			  	                      counter
//			  	                  );
//			  	              }
//
//			  	              encoderDebounce = HAL_GetTick();
//			  	          }
//			  	      }
//
//			  	      lastCLK = currentCLK;
			  	      /* =========================
//			  	         ENCODER BUTTON
//			  	         ========================= */
//
//			  	      static uint8_t lastButtonState = GPIO_PIN_SET;
//
//			  	      uint8_t currentButtonState =
//			  	          HAL_GPIO_ReadPin(
//			  	              GPIOB,
//			  	              GPIO_PIN_12
//			  	          );
//
//			  	      /* BUTTON PRESSED */
//
//			  	      if(currentButtonState == GPIO_PIN_RESET &&
//			  	         lastButtonState == GPIO_PIN_SET)
//			  	      {
//			  	          HAL_Delay(20);
//
//			  	          if(HAL_GPIO_ReadPin(
//			  	                 GPIOB,
//			  	                 GPIO_PIN_12
//			  	             ) == GPIO_PIN_RESET)
//			  	          {
//			  	              clicked = 1;
//
//			  	              printf(
//			  	                  "BTN:%d\r\n",
//			  	                  clicked
//			  	              );
//			  	          }
//			  	      }
//
//			  	      /* BUTTON RELEASED */
//
//			  	      else if(currentButtonState == GPIO_PIN_SET &&
//			  	              lastButtonState == GPIO_PIN_RESET)
//			  	      {
//			  	          clicked = 0;
//
//			  	          printf(
//			  	              "BTN:%d\r\n",
//			  	              clicked
//			  	          );
//			  	      }
//
//			  	      lastButtonState = currentButtonState;

			  	    /* =========================
			  	           COMPLETE UART DATA
			  	           ========================= */

			  	        sprintf(
			  	            msg,
			  	            "TEMP:%d,HUM:%d,LDR:%lu,TRACK:%d,RGB:%d,STATUS:%s\r\n",

			  	            (int)tCelsius,
			  	            (int)RH,
			  	            ldr,
			  	            track,
			  	            rgbState,
			  	            status
			  	        );

			  	        HAL_UART_Transmit(
			  	            &huart1,
			  	            (uint8_t*)msg,
			  	            strlen(msg),
			  	            100
			  	        );

			  	        HAL_Delay(500);
			  	    }

}

    /* USER CODE BEGIN 3 */
  /* USER CODE END 3 */


/**
  * @brief System Clock Configuration
  * @retval None
  */
void SystemClock_Config(void)
{
  RCC_OscInitTypeDef RCC_OscInitStruct = {0};
  RCC_ClkInitTypeDef RCC_ClkInitStruct = {0};
  RCC_PeriphCLKInitTypeDef PeriphClkInit = {0};

  /** Initializes the RCC Oscillators according to the specified parameters
  * in the RCC_OscInitTypeDef structure.
  */
  RCC_OscInitStruct.OscillatorType = RCC_OSCILLATORTYPE_HSE;
  RCC_OscInitStruct.HSEState = RCC_HSE_ON;
  RCC_OscInitStruct.HSEPredivValue = RCC_HSE_PREDIV_DIV1;
  RCC_OscInitStruct.HSIState = RCC_HSI_ON;
  RCC_OscInitStruct.PLL.PLLState = RCC_PLL_ON;
  RCC_OscInitStruct.PLL.PLLSource = RCC_PLLSOURCE_HSE;
  RCC_OscInitStruct.PLL.PLLMUL = RCC_PLL_MUL9;
  if (HAL_RCC_OscConfig(&RCC_OscInitStruct) != HAL_OK)
  {
    Error_Handler();
  }

  /** Initializes the CPU, AHB and APB buses clocks
  */
  RCC_ClkInitStruct.ClockType = RCC_CLOCKTYPE_HCLK|RCC_CLOCKTYPE_SYSCLK
                              |RCC_CLOCKTYPE_PCLK1|RCC_CLOCKTYPE_PCLK2;
  RCC_ClkInitStruct.SYSCLKSource = RCC_SYSCLKSOURCE_PLLCLK;
  RCC_ClkInitStruct.AHBCLKDivider = RCC_SYSCLK_DIV1;
  RCC_ClkInitStruct.APB1CLKDivider = RCC_HCLK_DIV2;
  RCC_ClkInitStruct.APB2CLKDivider = RCC_HCLK_DIV1;

  if (HAL_RCC_ClockConfig(&RCC_ClkInitStruct, FLASH_LATENCY_2) != HAL_OK)
  {
    Error_Handler();
  }
  PeriphClkInit.PeriphClockSelection = RCC_PERIPHCLK_ADC;
  PeriphClkInit.AdcClockSelection = RCC_ADCPCLK2_DIV6;
  if (HAL_RCCEx_PeriphCLKConfig(&PeriphClkInit) != HAL_OK)
  {
    Error_Handler();
  }
}

/**
  * @brief ADC1 Initialization Function
  * @param None
  * @retval None
  */
static void MX_ADC1_Init(void)
{

  /* USER CODE BEGIN ADC1_Init 0 */

  /* USER CODE END ADC1_Init 0 */

  ADC_ChannelConfTypeDef sConfig = {0};

  /* USER CODE BEGIN ADC1_Init 1 */

  /* USER CODE END ADC1_Init 1 */

  /** Common config
  */
  hadc1.Instance = ADC1;
  hadc1.Init.ScanConvMode = ADC_SCAN_DISABLE;
  hadc1.Init.ContinuousConvMode = DISABLE;
  hadc1.Init.DiscontinuousConvMode = DISABLE;
  hadc1.Init.ExternalTrigConv = ADC_SOFTWARE_START;
  hadc1.Init.DataAlign = ADC_DATAALIGN_RIGHT;
  hadc1.Init.NbrOfConversion = 1;
  if (HAL_ADC_Init(&hadc1) != HAL_OK)
  {
    Error_Handler();
  }

  /** Configure Regular Channel
  */
  sConfig.Channel = ADC_CHANNEL_0;
  sConfig.Rank = ADC_REGULAR_RANK_1;
  sConfig.SamplingTime = ADC_SAMPLETIME_1CYCLE_5;
  if (HAL_ADC_ConfigChannel(&hadc1, &sConfig) != HAL_OK)
  {
    Error_Handler();
  }
  /* USER CODE BEGIN ADC1_Init 2 */

  /* USER CODE END ADC1_Init 2 */

}

/**
  * @brief TIM1 Initialization Function
  * @param None
  * @retval None
  */
static void MX_TIM1_Init(void)
{

  /* USER CODE BEGIN TIM1_Init 0 */

  /* USER CODE END TIM1_Init 0 */

  TIM_MasterConfigTypeDef sMasterConfig = {0};
  TIM_OC_InitTypeDef sConfigOC = {0};
  TIM_BreakDeadTimeConfigTypeDef sBreakDeadTimeConfig = {0};

  /* USER CODE BEGIN TIM1_Init 1 */

  /* USER CODE END TIM1_Init 1 */
  htim1.Instance = TIM1;
  htim1.Init.Prescaler = 0;
  htim1.Init.CounterMode = TIM_COUNTERMODE_UP;
  htim1.Init.Period = 999;
  htim1.Init.ClockDivision = TIM_CLOCKDIVISION_DIV1;
  htim1.Init.RepetitionCounter = 0;
  htim1.Init.AutoReloadPreload = TIM_AUTORELOAD_PRELOAD_DISABLE;
  if (HAL_TIM_PWM_Init(&htim1) != HAL_OK)
  {
    Error_Handler();
  }
  sMasterConfig.MasterOutputTrigger = TIM_TRGO_RESET;
  sMasterConfig.MasterSlaveMode = TIM_MASTERSLAVEMODE_DISABLE;
  if (HAL_TIMEx_MasterConfigSynchronization(&htim1, &sMasterConfig) != HAL_OK)
  {
    Error_Handler();
  }
  sConfigOC.OCMode = TIM_OCMODE_PWM1;
  sConfigOC.Pulse = 0;
  sConfigOC.OCPolarity = TIM_OCPOLARITY_HIGH;
  sConfigOC.OCNPolarity = TIM_OCNPOLARITY_HIGH;
  sConfigOC.OCFastMode = TIM_OCFAST_DISABLE;
  sConfigOC.OCIdleState = TIM_OCIDLESTATE_RESET;
  sConfigOC.OCNIdleState = TIM_OCNIDLESTATE_RESET;
  if (HAL_TIM_PWM_ConfigChannel(&htim1, &sConfigOC, TIM_CHANNEL_2) != HAL_OK)
  {
    Error_Handler();
  }
  if (HAL_TIM_PWM_ConfigChannel(&htim1, &sConfigOC, TIM_CHANNEL_3) != HAL_OK)
  {
    Error_Handler();
  }
  if (HAL_TIM_PWM_ConfigChannel(&htim1, &sConfigOC, TIM_CHANNEL_4) != HAL_OK)
  {
    Error_Handler();
  }
  sBreakDeadTimeConfig.OffStateRunMode = TIM_OSSR_DISABLE;
  sBreakDeadTimeConfig.OffStateIDLEMode = TIM_OSSI_DISABLE;
  sBreakDeadTimeConfig.LockLevel = TIM_LOCKLEVEL_OFF;
  sBreakDeadTimeConfig.DeadTime = 0;
  sBreakDeadTimeConfig.BreakState = TIM_BREAK_DISABLE;
  sBreakDeadTimeConfig.BreakPolarity = TIM_BREAKPOLARITY_HIGH;
  sBreakDeadTimeConfig.AutomaticOutput = TIM_AUTOMATICOUTPUT_DISABLE;
  if (HAL_TIMEx_ConfigBreakDeadTime(&htim1, &sBreakDeadTimeConfig) != HAL_OK)
  {
    Error_Handler();
  }
  /* USER CODE BEGIN TIM1_Init 2 */

  /* USER CODE END TIM1_Init 2 */
  HAL_TIM_MspPostInit(&htim1);

}

/**
  * @brief TIM2 Initialization Function
  * @param None
  * @retval None
  */
static void MX_TIM2_Init(void)
{

  /* USER CODE BEGIN TIM2_Init 0 */

  /* USER CODE END TIM2_Init 0 */

  TIM_ClockConfigTypeDef sClockSourceConfig = {0};
  TIM_MasterConfigTypeDef sMasterConfig = {0};

  /* USER CODE BEGIN TIM2_Init 1 */

  /* USER CODE END TIM2_Init 1 */
  htim2.Instance = TIM2;
  htim2.Init.Prescaler = 71;
  htim2.Init.CounterMode = TIM_COUNTERMODE_UP;
  htim2.Init.Period = 65535;
  htim2.Init.ClockDivision = TIM_CLOCKDIVISION_DIV1;
  htim2.Init.AutoReloadPreload = TIM_AUTORELOAD_PRELOAD_DISABLE;
  if (HAL_TIM_Base_Init(&htim2) != HAL_OK)
  {
    Error_Handler();
  }
  sClockSourceConfig.ClockSource = TIM_CLOCKSOURCE_INTERNAL;
  if (HAL_TIM_ConfigClockSource(&htim2, &sClockSourceConfig) != HAL_OK)
  {
    Error_Handler();
  }
  sMasterConfig.MasterOutputTrigger = TIM_TRGO_RESET;
  sMasterConfig.MasterSlaveMode = TIM_MASTERSLAVEMODE_DISABLE;
  if (HAL_TIMEx_MasterConfigSynchronization(&htim2, &sMasterConfig) != HAL_OK)
  {
    Error_Handler();
  }
  /* USER CODE BEGIN TIM2_Init 2 */

  /* USER CODE END TIM2_Init 2 */

}

/**
  * @brief USART1 Initialization Function
  * @param None
  * @retval None
  */
static void MX_USART1_UART_Init(void)
{

  /* USER CODE BEGIN USART1_Init 0 */

  /* USER CODE END USART1_Init 0 */

  /* USER CODE BEGIN USART1_Init 1 */

  /* USER CODE END USART1_Init 1 */
  huart1.Instance = USART1;
  huart1.Init.BaudRate = 115200;
  huart1.Init.WordLength = UART_WORDLENGTH_8B;
  huart1.Init.StopBits = UART_STOPBITS_1;
  huart1.Init.Parity = UART_PARITY_NONE;
  huart1.Init.Mode = UART_MODE_TX_RX;
  huart1.Init.HwFlowCtl = UART_HWCONTROL_NONE;
  huart1.Init.OverSampling = UART_OVERSAMPLING_16;
  if (HAL_UART_Init(&huart1) != HAL_OK)
  {
    Error_Handler();
  }
  /* USER CODE BEGIN USART1_Init 2 */

  /* USER CODE END USART1_Init 2 */

}

/**
  * @brief GPIO Initialization Function
  * @param None
  * @retval None
  */
static void MX_GPIO_Init(void)
{
  GPIO_InitTypeDef GPIO_InitStruct = {0};
  /* USER CODE BEGIN MX_GPIO_Init_1 */

  /* USER CODE END MX_GPIO_Init_1 */

  /* GPIO Ports Clock Enable */
  __HAL_RCC_GPIOD_CLK_ENABLE();
  __HAL_RCC_GPIOA_CLK_ENABLE();
  __HAL_RCC_GPIOB_CLK_ENABLE();

  /*Configure GPIO pin Output Level */
  HAL_GPIO_WritePin(GPIOB, Buzzer_Pin|dht11_data_Pin, GPIO_PIN_RESET);

  /*Configure GPIO pins : Tracking_Pin CLK_Pin DT_Pin */
  GPIO_InitStruct.Pin = Tracking_Pin|CLK_Pin|DT_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_INPUT;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  HAL_GPIO_Init(GPIOB, &GPIO_InitStruct);

  /*Configure GPIO pin : SW_Pin */
  GPIO_InitStruct.Pin = SW_Pin|CLK_Pin|DT_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_INPUT;
  GPIO_InitStruct.Pull = GPIO_PULLUP;
  HAL_GPIO_Init(SW_GPIO_Port, &GPIO_InitStruct);

  /*Configure GPIO pins : Buzzer_Pin dht11_data_Pin */
  GPIO_InitStruct.Pin = Buzzer_Pin|dht11_data_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
  HAL_GPIO_Init(GPIOB, &GPIO_InitStruct);

  /* USER CODE BEGIN MX_GPIO_Init_2 */

  /* USER CODE END MX_GPIO_Init_2 */
}

/* USER CODE BEGIN 4 */

/* USER CODE END 4 */

/**
  * @brief  This function is executed in case of error occurrence.
  * @retval None
  */
void Error_Handler(void)
{
  /* USER CODE BEGIN Error_Handler_Debug */
  /* User can add his own implementation to report the HAL error return state */
  __disable_irq();
  while (1)
  {
  }
  /* USER CODE END Error_Handler_Debug */
}
#ifdef USE_FULL_ASSERT
/**
  * @brief  Reports the name of the source file and the source line number
  *         where the assert_param error has occurred.
  * @param  file: pointer to the source file name
  * @param  line: assert_param error line source number
  * @retval None
  */
void assert_failed(uint8_t *file, uint32_t line)
{
  /* USER CODE BEGIN 6 */
  /* User can add his own implementation to report the file name and line number,
     ex: printf("Wrong parameters value: file %s on line %d\r\n", file, line) */
  /* USER CODE END 6 */
}
#endif /* USE_FULL_ASSERT */
