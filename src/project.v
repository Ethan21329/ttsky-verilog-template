/*
 * Copyright (c) 2024 Your Name
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none

module project (
    input  wire [7:0] ui_in,    // Dedicated inputs
    output wire [7:0] uo_out,   // Dedicated outputs
    input  wire [7:0] uio_in,   // IOs: Input path
    output wire [7:0] uio_out,  // IOs: Output path
    output wire [7:0] uio_oe,   // IOs: Enable path (active high: 0=input, 1=output)
    input  wire       ena,      // always 1 when the design is powered, so you can ignore it
    input  wire       clk,      // clock
    input  wire       rst_n     // reset_n - low to reset
);
  // unused signals
  assign uio_out = 8'h00;
  assign uio_oe = 8'h00;

  // input text
  wire [7:0] text_i = ui_in;

  // Encryption key with MSB hard coded to 0
  wire [7:0] encrypt_key = {1'b0, uio_in[6:0]}; 

  // mode = 1 encrypt , mode = 0 decrypt
  wire mode = uio_in[7];

  function [7:0] left_rotate;
    input [7:0] x;
    left_rotate = {x[4:0], x[7:5]};
  endfunction

  function [7:0] right_rotate;
    input [7:0] x;
    right_rotate = {x[2:0], x[7:3]};
  endfunction

  function [7:0] encrypt;
    input [7:0] x;
    input [7:0] key;
    input [7:0] r;
    encrypt = (left_rotate(x ^ key) + key) ^ r;
  endfunction

  function [7:0] decrypt;
    input [7:0] x;
    input [7:0] key;
    input [7:0] r;
    decrypt = right_rotate((x ^ r) - key) ^ key;
  endfunction

  wire [7:0] r1 = 8'b10001001;
  wire [7:0] r2 = 8'b11110111;
  wire [7:0] r3 = 8'b11110001;
  wire [7:0] r4 = 8'b01110101;

  reg [7:0] comb_out;
  reg [7:0] temp;

  always @(*) begin
    if (mode) begin
      temp = encrypt(text_i, encrypt_key, r1);
      temp = encrypt(temp, encrypt_key, r2);
      temp = encrypt(temp, encrypt_key, r3);
      comb_out = encrypt(temp, encrypt_key, r4);
    end else begin
      temp = decrypt(text_i, encrypt_key, r4);
      temp = decrypt(temp, encrypt_key, r3);
      temp = decrypt(temp, encrypt_key, r2);
      comb_out = decrypt(temp, encrypt_key, r1);
    end
  end

  reg [7:0] data_o;

  always @(posedge clk) begin
    if (!rst_n) begin
      data_o <= 8'h00;
    end else begin
      data_o <= comb_out;
    end
  end

  assign uo_out = data_o;



endmodule
